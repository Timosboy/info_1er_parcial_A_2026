import math
import logging
import arcade
import pymunk

from game_object import Bird, Column, Pig, YellowBird, BlueBird, PajaroExplosivo, PajaroRayo
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1200
HEIGHT = 700
TITLE = "Angry birds"
GRAVITY = -900

BIRD_NAMES = {
    "Bird": "Rojo (basico)",
    "YellowBird": "Amarillo - Turbo [clic der]",
    "BlueBird": "Azul - Divide x3 [clic der]",
    "PajaroExplosivo": "Explosivo - Boom [clic der]",
    "PajaroRayo": "Rayo - Laser [clic der]",
}


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")
        # crear espacio de pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        # agregar piso
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        self.add_columns()
        self.add_pigs()

        self.start_point = Point2D()
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False

        self.tipos_pajaros = [Bird, YellowBird, BlueBird, PajaroExplosivo, PajaroRayo]
        self.indice_pajaro = 0
        self.pajaro_volando = None

        # agregar un collision handler
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in self.world:
                if obj.shape in arbiter.shapes:
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)

        return True

    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)  # actualiza la simulacion de las fisicas
        self.sprites.update(delta_time)

    def _activar_habilidad(self):
        if isinstance(self.pajaro_volando, YellowBird):
            self.pajaro_volando.activar()
        elif isinstance(self.pajaro_volando, BlueBird):
            self.pajaro_volando.dividir(self.space, self.sprites, self.birds)
        elif isinstance(self.pajaro_volando, PajaroExplosivo):
            self.pajaro_volando.explotar()
        elif isinstance(self.pajaro_volando, PajaroRayo):
            self.pajaro_volando.disparar_rayo(self.sprites, self.world)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start_point = Point2D(x, y)
            self.end_point = Point2D(x, y)
            self.draw_line = True
            logger.debug(f"Start Point: {self.start_point}")
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if self.pajaro_volando and self.pajaro_volando.body.velocity.length > 10:
                self._activar_habilidad()

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line:
            logger.debug(f"Releasing from: {self.end_point}")
            self.draw_line = False
            vector_impulso = get_impulse_vector(self.start_point, self.end_point)
            tipo = self.tipos_pajaros[self.indice_pajaro % len(self.tipos_pajaros)]
            if tipo == Bird:
                self.pajaro_volando = Bird(
                    "assets/img/red-bird3.png", vector_impulso,
                    self.start_point.x, self.start_point.y, self.space,
                )
            else:
                self.pajaro_volando = tipo(
                    vector_impulso, self.start_point.x, self.start_point.y, self.space,
                )
            self.sprites.append(self.pajaro_volando)
            self.birds.append(self.pajaro_volando)
            self.indice_pajaro += 1

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()
        if self.draw_line:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)
        self._draw_hud()

    def _draw_hud(self):
        tipo_actual = self.tipos_pajaros[self.indice_pajaro % len(self.tipos_pajaros)]
        nombre_actual = BIRD_NAMES.get(tipo_actual.__name__, tipo_actual.__name__)
        tipo_sig = self.tipos_pajaros[(self.indice_pajaro + 1) % len(self.tipos_pajaros)]
        nombre_sig = BIRD_NAMES.get(tipo_sig.__name__, tipo_sig.__name__)

        arcade.draw_rect_filled(arcade.XYWH(110, HEIGHT - 40, 220, 70), (0, 0, 0, 140))
        arcade.draw_text(f"Siguiente: {nombre_actual}", 10, HEIGHT - 30,
                         arcade.color.YELLOW, 13, bold=True)
        arcade.draw_text(f"Despues:   {nombre_sig}", 10, HEIGHT - 50,
                         arcade.color.WHITE, 11)
        arcade.draw_text(f"Disparos: {self.indice_pajaro}", 10, HEIGHT - 68,
                         arcade.color.LIGHT_GRAY, 10)
        arcade.draw_text("Clic izq+arrastra=lanzar | Clic der=habilidad",
                         10, 20, arcade.color.WHITE, 11)


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()