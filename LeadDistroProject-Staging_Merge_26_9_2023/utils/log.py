from dashboard.models import Activity

def create_log_activity(user_id, description):
    Activity.objects.create(user_id=user_id, actions='created', description=description)

def update_log_activity(user_id, description):
    Activity.objects.create(user_id=user_id, actions='updated', description=description)

def delete_log_activity(user_id, description):
    Activity.objects.create(user_id=user_id, actions='deleted', description=description)
