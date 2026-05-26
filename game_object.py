import math
import arcade
import pymunk
from game_logic import ImpulseVector


class Bird(arcade.Sprite):
    """
    Bird class. This represents an angry bird. All the physics is handled by Pymunk,
    the init method only set some initial properties
    """
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 300,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
        scale: float = 1,
    ):
        super().__init__(image_path, scale)
        # body
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        impulse_pymunk = impulse * pymunk.Vec2d(1, 0)
        # apply impulse
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))
        # shape
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape

    def update(self, delta_time):
        """
        Update the position of the bird sprite based on the physics body position
        """
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class PassiveObject(arcade.Sprite):
    """
    Passive object that can interact with other objects.
    """
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class YellowBird(Bird):
    def __init__(self, vector_impulso, x, y, espacio, **kwargs):
        super().__init__("assets/img/rayo.png", vector_impulso, x, y, espacio, scale=0.08, **kwargs)
        self.turbo_usado = False

    def activar(self):
        if self.turbo_usado:
            return
        self.turbo_usado = True
        vel_actual = self.body.velocity
        self.body.apply_impulse_at_local_point(vel_actual * self.body.mass)


class BlueBird(Bird):
    def __init__(self, vector_impulso, x, y, espacio, **kwargs):
        super().__init__("assets/img/blue.png", vector_impulso, x, y, espacio, scale=0.18, **kwargs)
        self.dividido = False

    def dividir(self, espacio, sprites, pajaros):
        if self.dividido:
            return
        self.dividido = True
        vel = self.body.velocity
        magnitud = vel.length
        angulo_actual = math.atan2(vel.y, vel.x)
        for delta in [math.radians(30), math.radians(-30)]:
            angulo_nuevo = angulo_actual + delta
            nuevo = BlueBird(ImpulseVector(0, 0), self.center_x, self.center_y, espacio)
            nuevo.dividido = True
            nuevo.body.velocity = pymunk.Vec2d(
                magnitud * math.cos(angulo_nuevo),
                magnitud * math.sin(angulo_nuevo),
            )
            sprites.append(nuevo)
            pajaros.append(nuevo)


class PajaroExplosivo(Bird):
    def __init__(self, vector_impulso, x, y, espacio, **kwargs):
        super().__init__("assets/img/explosivo.png", vector_impulso, x, y, espacio, scale=0.08, **kwargs)
        self.explotado = False
        self.radio = 150
        self.fuerza = 8000

    def explotar(self):
        if self.explotado:
            return
        self.explotado = True
        pos = self.body.position
        for forma in self.body.space.shapes:
            if forma.body == self.body or forma.body.body_type != pymunk.Body.DYNAMIC:
                continue
            diferencia = forma.body.position - pos
            distancia = diferencia.length
            if 0 < distancia < self.radio:
                magnitud = self.fuerza * (1 - distancia / self.radio)
                forma.body.apply_impulse_at_world_point(
                    diferencia.normalized() * magnitud,
                    forma.body.position,
                )


class PajaroRayo(Bird):
    def __init__(self, vector_impulso, x, y, espacio, **kwargs):
        super().__init__("assets/img/rayaso.png", vector_impulso, x, y, espacio, scale=0.04, **kwargs)
        self.rayo_disparado = False

    def disparar_rayo(self, sprites, world):
        if self.rayo_disparado:
            return
        self.rayo_disparado = True
        pos = self.body.position
        direccion = self.body.velocity.normalized()
        punto_fin = pos + direccion * 2000
        impactos = self.body.space.segment_query(pos, punto_fin, 5, pymunk.ShapeFilter())
        formas_golpeadas = {hit.shape for hit in impactos if hit.shape != self.shape}
        for obj in list(world):
            if hasattr(obj, "shape") and obj.shape in formas_golpeadas:
                obj.remove_from_sprite_lists()
                try:
                    self.body.space.remove(obj.shape, obj.body)
                except Exception:
                    pass
