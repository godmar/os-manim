
You are in a venv with manim (0.22.0, community edition) installed.

Let's develop a visualization of how multiple threads acquire and release locks.
The visualization should visualize the following aspects

- solution to critical section problem and providing mutual exclusion
- relationship between locks and the data they protect
- scenarios with multiple threads
- scenarios with multiple pieces of data
- risks: 
    - data races when forgetting to acquire a lock, or acquiring the wrong lock
    - deadlock when forgetting to release a lock

- the visualization shall distinguish between a lock internals and the externally 
  provided abstraction. If in doubt, keep details abstracted away.

