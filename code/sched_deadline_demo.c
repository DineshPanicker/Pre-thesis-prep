/* sched_deadline_demo.c — minimal SCHED_DEADLINE periodic task. */
#define _GNU_SOURCE // Tells glibc to expose linux specific extensions. w/o this clock_nanosleep flag wont be declared
#include <linux/sched.h>
#include <linux/types.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

/* glibc may not yet wrap these — declare them ourselves. */
struct sched_attr
{
    __u32 size;
    __u32 sched_policy;
    __u64 sched_flags;
    __s32 sched_nice;
    __u32 sched_priority;
    /*
    These three
    parameters define a deadline task in nanoseconds
    */
    __u64 sched_runtime;
    /*
   These three
   parameters define a deadline task in nanoseconds
   */
    __u64 sched_deadline;
    /*
   These three
   parameters define a deadline task in nanoseconds
   */
    __u64 sched_period;
};
// the above struct tells how the kernel takes scheduling parameters from a userspace program.

static int sched_setattr_(pid_t pid, const struct sched_attr *attr, unsigned int flags)
{
    return syscall(SYS_sched_setattr, pid, attr, flags);
}
// this is setting up sched_deadline(EDF) algorithm

#define SCHED_DEADLINE 6
#define PERIOD_NS (1000L * 1000L) // 1ms

int main(void)
{
    // Locking all the pages so we never page-fault during the loop
    // keeps all of the program's current and future memroy pages permanently locked into the physical RAM

    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0)
    {
        perror("mlockall");
        return 1;
    }

    /**
     * Declare ourselves a periodic deadline task
     * runtime = 200us
     * deadline = 1000 us
     * period = 1000 us
     */
    struct sched_attr attr = {0};

    attr.size = sizeof(attr);
    attr.sched_policy = SCHED_DEADLINE; // use EDF based scheduling
    attr.sched_runtime = 200 * 1000;
    attr.sched_deadline = 1000 * 1000;
    attr.sched_period = 1000 * 1000;

    if (sched_setattr_(0, &attr, 0) != 0)
    {
        fprintf(stderr, "sched_setattr: %s\n", strerror(errno));
        return 1;
    }
    // passes these rules to the kernel for process ID 0(current thread)

    struct timespec next;
    clock_gettime(CLOCK_MONOTONIC, &next); // the clock monotonic reads a clock that represents the absolute elapsed time since the system booted which then saves the current exact time into the next variable

    for (int i = 0; i < 1000; i++)
    {
        next.tv_nsec += PERIOD_NS;
        while (next.tv_nsec >= 1000000000L)
        {
            next.tv_nsec -= 1000000000L;
            next.tv_nsec += 1;
        }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL); // firstly use system clock as the baseline,switch the kernel behaviour to absolute time
        // then keep this thread suspended until the clock reaches the exact timestamp stored in the next structure
    }
    printf("1000 cycles completed under SCHED_DEADLINE(Earliest deadline first) algorithm\n");
    return 0;
}