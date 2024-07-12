import logging

from django.conf import settings
from firebase_admin import credentials, db
from pyfcm import FCMNotification
from users.models import Device, Notification


def send_push_notification(user, title, message, notification, shipment_id):
    devices = Device.objects.filter(user=user)
    registration_ids = devices.values_list("registration_id", flat=True)
    push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)

    result = push_service.notify_multiple_devices(
        registration_ids=list(registration_ids),
        message_title=title,
        message_body=message,
        data_message={
            "type": notification.type,
            "shipment_id": shipment_id,
        },
    )

    notifications_ref = db.reference(f"notifications/{user.id}")
    new_notification_ref = notifications_ref.push()
    new_notification_ref.set(
        {
            "title": title,
            "message": message,
            "read": False,  # Mark as unread initially
            "timestamp": {".sv": "timestamp"},  # Use Firebase server timestamp
        }
    )
    return result


def create_and_send_notification(recipient, title, message, status, shipment_id):
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        type=status,
        read=False,
        shipment_id=shipment_id,
        data={"shipment_id": shipment_id, "type": status},
    )
    send_push_notification(recipient, title, message, notification, shipment_id)
    logging.warning("Notification sent to: {}".format(recipient))


# from pyfcm import FCMNotification

# push_service = FCMNotification(api_key="<api-key>")

# registration_id = "<device registration_id>"
# message_title = "Uber update"
# message_body = "Hi john, your customized news for today is ready"
# result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
# print result
