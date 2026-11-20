# libkernel

## remove Thread CPU time on macOS

## change Thread CPU time on macOS

- Thread CPU time on macOS (`clock_gettime` with the thread CPU clock, `getrusage` for a thread and the CPU time of a guest thread) comes from the Mach `thread_info` of the thread, which has microsecond resolution; `getrusage` for a thread fills only the user and system times.
