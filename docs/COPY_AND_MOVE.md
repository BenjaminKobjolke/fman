# Copy and Move

How fman's built-in Copy (F5) and Move (F6) find the files to transfer and
transfer them, and why the two run at the same time.

Both commands are `FileTreeOperation` subclasses (`CopyFiles`, `MoveFiles`) in
`src/main/resources/base/Plugins/Core/core/fileoperations.py`. The robocopy
variants are separate and described in [ROBOCOPY.md](ROBOCOPY.md).

## Two threads: gathering and transferring

Copying a folder means walking the tree first: which files are there, does the
destination already hold one of them, how big is each. On a local drive that
is quick. On a remote file system, an FTP server for example, every folder
costs a round trip, and a large tree can take minutes to walk.

fman used to finish that walk before transferring anything. The progress
dialog sat on "Gathering files..." and then "Preparing to copy N files" while
nothing moved.

Now the walk runs on its own thread and transfers start as soon as the first
file is found:

```
gathering thread                       transferring thread
----------------                       -------------------
_gather_files()                        _run_gathered_tasks()
  checks, makedirs(destination)          queue.get() ──► run task
  per source: prepare_copy(...) ──►      queue.get() ──► run task
    overwrite prompt if needed  queue    ...
  ...                                    _DONE ──► finished
  queue.put(_DONE)
```

- **The gathering thread** (`_gather_in_background`) runs the same
  `_gather_files()` as before. `_enqueue(...)` puts each task on a `Queue` the
  moment the file system yields it, instead of collecting them in a list.
- **The transferring thread** is the command's own worker thread. It takes
  tasks off the queue and runs them with the same error handling as before.
- **`_DONE`** always ends the queue, however the gathering stopped: done,
  canceled, aborted or crashed. An exception raised while gathering is stored
  and raised again once the transfers have ended.

## Details that follow from it

- **The progress bar total grows.** Nobody knows the total size while the walk
  is still running, so each task's size is added to the total when it starts.
  The bar still ends at 100%.
- **One task of look-ahead.** Before running a task, the transferring thread
  waits until the queue holds its next item, without taking it. That is how
  it knows a failing task is the last one, which decides whether the error
  prompt offers `OK` or `Yes / Yes to all / Abort`.
- **One prompt at a time.** Overwrite prompts come from the gathering thread,
  error prompts from the transferring one. Without a lock the second modal
  dialog would open inside the first's event loop. `_alert_lock` is held
  around both `_should_overwrite(...)` and `_handle_exception(...)`.
- **Stopping.** Cancel is seen by both threads. When the transfers end early
  (Abort on an error prompt), `_stop_gathering` makes `_iter(...)` stop the
  walk, and the transferring thread waits for the gathering thread before it
  returns.
- **Abort on an overwrite prompt** stops the queued tasks that have not started
  yet. Files transferred before that point stay transferred, the same as an
  Abort on an error prompt mid-copy.

## Parallel workers

A file system can ask for several transferring threads: Copy asks
`fman.fs.get_parallel_transfers(src, dest)`, which takes the larger answer of
the source and destination file system. The base `FileSystem` answers 1. The
FTP plugin answers 3 between FTP and this machine, so downloads and uploads run
three files at once, each on its own connection. Move always uses one worker:
a directory is post-processed once the moves queued before it are done.

`TransferWorkers` (`core/transfer_workers.py`) runs the queue:

- **One worker runs on the command's thread**, exactly as before. Several
  run on threads of their own, and the progress dialog lists them: one line
  per worker with its file and percentage, and `−` / `+` buttons
  (`Task.show_workers(...)`, drawn by `fman/impl/workers_label.py`).
- **`+`** starts another worker, up to 10. **`−`** marks the newest worker
  retiring: it finishes its active file and then stops. A worker that was
  waiting for a file runs the one it gets, then stops. At least one worker
  always stays.
- **`_DONE` stays in the queue.** A worker that draws it puts it back, so
  every worker sees it.
- **The look-ahead does not take the next task**, since another worker may
  run it. With several workers, "last" means nothing more is queued yet. If
  several workers wait on the queue, one `put(...)` wakes only one of them, so
  a worker that wakes passes the wakeup on.
- **Progress is added, not set.** `ChildProgressDialog` sets the parent's
  progress absolutely, which parallel tasks would overwrite. Each task runs
  with a `WorkerProgress` that adds its change instead, under
  `_progress_lock`. The GUI thread never takes that lock, because
  `set_size(...)` waits for the GUI thread while holding it.
- **An Abort or an error in one worker stops all of them** before their next
  task, and also stops the walk, which the other workers would otherwise wait
  for.

## What a file system plugin has to do

Streaming only helps if `prepare_copy(...)` hands tasks out one at a time. Return
a generator, not a list:

```python
def prepare_copy(self, src_url, dst_url):
	# Raise here, not on the first iteration: fman tries the other file
	# system only when this call itself raises UnsupportedOperation.
	if not self._can_copy(src_url, dst_url):
		raise UnsupportedOperation
	return self._prepare_copy(src_url, dst_url)

def _prepare_copy(self, src_url, dst_url):
	if not self.is_dir(src_url):
		yield CopyFile(...)
		return
	yield Task('Creating ...', fn=self.mkdir, ...)
	for name in self.iterdir(src_url):
		yield from self._prepare_copy(join(src_url, name), join(dst_url, name))
```

`LocalFileSystem` (`core/fs/local/__init__.py`) and the FTP plugin both work
this way. A plugin that returns a list still works, just without streaming
for that folder.

`prepare_copy(...)` is now called from the gathering thread, and the tasks run
on other threads. A plugin that keeps connections per thread opens one for the
walk and one per worker. The FTP plugin does this, so a server that limits
connections per IP may refuse some. The user can press `−` in the progress
dialog.

## Tests

`core/tests/test_fileoperations.py` covers overwrite and error prompts, abort
and move-to-self. `StreamingTransferTest` checks that a transfer starts while
gathering is still running: its file system's `iterdir(...)` waits until a
copy has started, and gives up after 5 seconds, so a sequential version fails
the test instead of hanging the run. `ParallelTransferTest` does the same for
workers: each copy waits until all of them have started.
`core/tests/test_transfer_workers.py` covers adding, removing, aborting and
errors.

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\fman'; cmd /c '.\tools\run_core_tests.bat'"
```

The worker rows and buttons are tested in
`fman_unittest/impl/progress_dialog_test.py`, via
`tools\run_progress_dialog_tests.bat`.
