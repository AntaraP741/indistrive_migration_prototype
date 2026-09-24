from math import cos, radians, sin
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 800
HEIGHT = 800
BG = (248, 250, 252)
AXIS = (180, 190, 205)
BLACK = (20, 24, 28)
BLUE = (37, 99, 235)
RED = (220, 38, 38)
GREEN = (22, 163, 74)
ORANGE = (249, 115, 22)
PURPLE = (126, 34, 206)
TEAL = (13, 148, 136)

OUTPUT_DIR = Path(__file__).resolve().parent / "output_images"


class PixelCanvas:
    def __init__(self, width=WIDTH, height=HEIGHT, bg=BG):
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (width, height), bg)
        self.pixels = self.image.load()
        self.draw = ImageDraw.Draw(self.image)

    def to_screen(self, x, y):
        return int(round(self.width / 2 + x)), int(round(self.height / 2 - y))

    def put_pixel(self, x, y, color=BLACK, size=1):
        sx, sy = self.to_screen(x, y)
        half = max(size // 2, 0)
        for dx in range(-half, half + 1):
            for dy in range(-half, half + 1):
                px = sx + dx
                py = sy + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    self.pixels[px, py] = color

    def draw_axes(self):
        self.draw.line((0, self.height / 2, self.width, self.height / 2), fill=AXIS)
        self.draw.line((self.width / 2, 0, self.width / 2, self.height), fill=AXIS)

    def write_title(self, title):
        self.draw.text((20, 20), title, fill=BLACK)

    def save(self, name):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / name
        self.image.save(path)
        return path


def bresenham_line(canvas, x1, y1, x2, y2, color=BLUE):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        canvas.put_pixel(x1, y1, color, size=2)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def midpoint_circle(canvas, xc, yc, radius, color=RED):
    x = 0
    y = radius
    p = 1 - radius

    while x <= y:
        for px, py in (
            (xc + x, yc + y),
            (xc - x, yc + y),
            (xc + x, yc - y),
            (xc - x, yc - y),
            (xc + y, yc + x),
            (xc - y, yc + x),
            (xc + y, yc - x),
            (xc - y, yc - x),
        ):
            canvas.put_pixel(px, py, color, size=2)

        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1


def polygon_edges(vertices):
    return list(zip(vertices, vertices[1:] + [vertices[0]]))


def scanline_fill(canvas, vertices, fill_color=GREEN, border_color=BLACK):
    ys = [y for _, y in vertices]
    y_min = int(min(ys))
    y_max = int(max(ys))

    for y in range(y_min, y_max + 1):
        intersections = []
        for (x1, y1), (x2, y2) in polygon_edges(vertices):
            if y1 == y2:
                continue
            if y >= min(y1, y2) and y < max(y1, y2):
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                intersections.append(x)

        intersections.sort()
        for i in range(0, len(intersections), 2):
            if i + 1 >= len(intersections):
                break
            start_x = int(round(intersections[i]))
            end_x = int(round(intersections[i + 1]))
            span = max(end_x - start_x, 1)
            for offset, x in enumerate(range(start_x, end_x + 1)):
                blend = offset / span
                color = (
                    int(fill_color[0] * (1 - blend) + ORANGE[0] * blend),
                    int(fill_color[1] * (1 - blend) + ORANGE[1] * blend),
                    int(fill_color[2] * (1 - blend) + ORANGE[2] * blend),
                )
                canvas.put_pixel(x, y, color)

    for (x1, y1), (x2, y2) in polygon_edges(vertices):
        bresenham_line(canvas, int(x1), int(y1), int(x2), int(y2), border_color)


def koch_curve(p1, p2, depth):
    if depth == 0:
        return [p1, p2]

    x1, y1 = p1
    x2, y2 = p2
    dx = (x2 - x1) / 3
    dy = (y2 - y1) / 3

    a = (x1 + dx, y1 + dy)
    b = (x1 + 2 * dx, y1 + 2 * dy)

    angle = radians(60)
    px = a[0] + (dx * cos(angle) - dy * sin(angle))
    py = a[1] + (dx * sin(angle) + dy * cos(angle))
    peak = (px, py)

    parts = [
        koch_curve(p1, a, depth - 1)[:-1],
        koch_curve(a, peak, depth - 1)[:-1],
        koch_curve(peak, b, depth - 1)[:-1],
        koch_curve(b, p2, depth - 1),
    ]

    combined = []
    for part in parts:
        combined.extend(part)
    return combined


def draw_polyline(canvas, points, color=PURPLE):
    for start, end in zip(points, points[1:]):
        bresenham_line(
            canvas,
            int(round(start[0])),
            int(round(start[1])),
            int(round(end[0])),
            int(round(end[1])),
            color,
        )


def apply_transform(point, matrix):
    x, y = point
    return (
        x * matrix[0][0] + y * matrix[0][1] + matrix[0][2],
        x * matrix[1][0] + y * matrix[1][1] + matrix[1][2],
    )


def transform_shape(points, matrix):
    return [apply_transform(point, matrix) for point in points]


def translation_matrix(tx, ty):
    return [[1, 0, tx], [0, 1, ty], [0, 0, 1]]


def scaling_matrix(sx, sy):
    return [[sx, 0, 0], [0, sy, 0], [0, 0, 1]]


def rotation_matrix(angle_deg):
    angle = radians(angle_deg)
    return [
        [cos(angle), -sin(angle), 0],
        [sin(angle), cos(angle), 0],
        [0, 0, 1],
    ]


def multiply_3x3(a, b):
    result = [[0, 0, 0] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            result[i][j] = sum(a[i][k] * b[k][j] for k in range(3))
    return result


def draw_shape(canvas, points, color):
    closed = points + [points[0]]
    draw_polyline(canvas, closed, color)


def generate_line_output():
    canvas = PixelCanvas()
    canvas.draw_axes()
    canvas.write_title("Bresenham Line Drawing Algorithm")
    lines = [
        (-300, -120, 260, 210, BLUE),
        (-250, 200, 280, 50, TEAL),
        (-100, -260, 180, 260, PURPLE),
    ]
    for x1, y1, x2, y2, color in lines:
        bresenham_line(canvas, x1, y1, x2, y2, color)
    return canvas.save("01_bresenham_line.png")


def generate_circle_output():
    canvas = PixelCanvas()
    canvas.draw_axes()
    canvas.write_title("Midpoint Circle Drawing Algorithm")
    midpoint_circle(canvas, 0, 0, 220, RED)
    midpoint_circle(canvas, 0, 0, 120, BLUE)
    midpoint_circle(canvas, 160, 120, 70, TEAL)
    return canvas.save("02_midpoint_circle.png")


def generate_fill_output():
    canvas = PixelCanvas()
    canvas.draw_axes()
    canvas.write_title("Scanline Polygon Fill / Shading")
    polygon = [(-220, -180), (-60, 200), (130, 220), (240, 20), (80, -210)]
    scanline_fill(canvas, polygon, fill_color=GREEN, border_color=BLACK)
    return canvas.save("03_scanline_fill.png")


def generate_fractal_output():
    canvas = PixelCanvas()
    canvas.draw_axes()
    canvas.write_title("Koch Curve Fractal")
    points = koch_curve((-300, -50), (300, -50), depth=4)
    draw_polyline(canvas, points, PURPLE)
    return canvas.save("04_koch_fractal.png")


def generate_transform_output():
    canvas = PixelCanvas()
    canvas.draw_axes()
    canvas.write_title("2D Transformations: Translation + Rotation + Scaling")

    square = [(-80, -80), (80, -80), (80, 80), (-80, 80)]
    draw_shape(canvas, square, BLACK)

    matrix = multiply_3x3(
        translation_matrix(190, 120),
        multiply_3x3(rotation_matrix(35), scaling_matrix(1.6, 0.9)),
    )
    transformed = transform_shape(square, matrix)
    draw_shape(canvas, transformed, BLUE)

    return canvas.save("05_transformations.png")


def main():
    outputs = [
        generate_line_output(),
        generate_circle_output(),
        generate_fill_output(),
        generate_fractal_output(),
        generate_transform_output(),
    ]

    print("Generated output images:")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
