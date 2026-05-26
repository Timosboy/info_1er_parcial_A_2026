import math
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ImpulseVector:
    angle: float
    impulse: float


@dataclass
class Point2D:
    x: float = 0
    y: float = 0


def get_angle_radians(point_a: Point2D, point_b: Point2D) -> float:
    return math.atan2(point_b.y - point_a.y, point_b.x - point_a.x)


def get_distance(point_a: Point2D, point_b: Point2D) -> float:
    return math.hypot(point_b.x - point_a.x, point_b.y - point_a.y)


def get_impulse_vector(start_point: Point2D, end_point: Point2D) -> ImpulseVector:
    angulo = get_angle_radians(end_point, start_point)
    magnitud = get_distance(start_point, end_point)
    return ImpulseVector(angulo, magnitud)
