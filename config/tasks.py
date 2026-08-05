from celery import shared_task


@shared_task(bind=True, ignore_result=True)
def debug_task(self):
    print("--------------------------")
    print("|    Celery Working      |")
    print("--------------------------")
