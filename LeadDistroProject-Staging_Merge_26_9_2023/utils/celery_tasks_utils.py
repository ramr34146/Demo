from leads.celery import app


def terminateTask(task_id):
    app.control.revoke(task_id, terminate=True, signal='SIGKILL')
    return None 