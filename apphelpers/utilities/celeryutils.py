from kombu import Queue
from celery import Celery as BaseCelery


class Celery(BaseCelery):
    def add_task_queues(self, *queues):
        self.conf.task_queues = tuple(Queue(queue) for queue in queues if queue)

    def set_default_queue(self, queue):
        self.conf.task_default_queue = queue

    def add_periodic_task(
        self,
        schedule,
        task,
        queue=None,
        autoretry_for=tuple(),
        max_retries=3,
        default_retry_delay=180,
    ):
        """
        queue:
            The celery queue to which the receiver should respond.
        task:
            The name of the task to execute.
        schedule:
            The frequency of execution.
            This can be the number of seconds as an integer, a timedelta, or a crontab.
            You can also define your own custom schedule types, by extending the
            interface of schedule.
        autoretry_for:
            A list/tuple of exception classes. By default, no exceptions will be
            autoretried.
        max_retries:
            Maximum number of retries before giving up. A value of None means task will
            retry forever. By default, this option is set to 3.
        default_retry_delay:
            Default time in seconds before a retry of the task should be executed.
            Can be either int or float. Default is a three minute delay.
        """
        super().add_periodic_task(
            schedule,
            self.task(
                task,
                autoretry_for=autoretry_for,
                max_retries=max_retries,
                default_retry_delay=default_retry_delay,
            )
            .s()
            .set(queue=queue),
        )

    def task_with_apply_async(self, countdown=0, retry=True, queue=None, **task_kwargs):
        """Executes function asynchronously.
        Not using apply_async means that the task will not be executed by a celery
        worker, but in the current process instead just like a normal synchronous
        function.
        countdown -- executes in specified no of seconds from now.
        retry -- configures retry behavior.
        """

        def wrap(f):
            task = self.task(f, **task_kwargs)

            def wrapped_f(*args, **kwargs):
                return task.apply_async(
                    args, kwargs, countdown=countdown, retry=retry, queue=queue
                )

            return wrapped_f

        return wrap

    def clear_all_tasks(self):
        """
        Removes all pending tasks
        """
        return self.control.purge()
