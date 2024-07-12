from enum import Enum


class ShipmentStatus(Enum):
    CONTAINER_QUEUED = "Queued"
    CONTAINER_ASSIGNED = "Assigned"
    PICKED_UP = "Picked Up"
    DELIVERED = "Delivered"
    ACCEPTED = "Accepted"
    RETURNED_EMPTY = "Returned Empty"
