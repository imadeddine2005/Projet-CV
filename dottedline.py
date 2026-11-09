import cv2


def drawline(img, pt1, pt2, color, thickness=1, style='dotted', gap=20):
    x1, y1 = pt1
    x2, y2 = pt2
    dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5  # Compute once
    if dist == 0 or img is None:
        return  # Avoid division by zero / null image
    if gap < 1:
        gap = 1

    if style == 'dotted':
        steps = int(dist / gap) + 1
        for i in range(steps):
            r = i / (steps - 1) if steps > 1 else 0
            x = int(x1 * (1 - r) + x2 * r + 0.5)
            y = int(y1 * (1 - r) + y2 * r + 0.5)
            cv2.circle(img, (x, y), thickness, color, -1)
    else:
        # Solid line with alternating segments
        steps = int(dist / gap) + 1
        prev_x, prev_y = x1, y1
        for i in range(1, steps):
            r = i / (steps - 1) if steps > 1 else 0
            x = int(x1 * (1 - r) + x2 * r + 0.5)
            y = int(y1 * (1 - r) + y2 * r + 0.5)
            if i % 2 == 1:
                cv2.line(img, (prev_x, prev_y), (x, y), color, thickness)
            prev_x, prev_y = x, y


def drawpoly(img, pts, color, thickness=1, style='dotted'):
    if len(pts) < 2:
        return
    for i in range(len(pts) - 1):
        drawline(img, pts[i], pts[i + 1], color, thickness, style)
    drawline(img, pts[-1], pts[0], color, thickness, style)  # Close the polygon


def drawrect(img, pt1, pt2, color, thickness=1, style='dotted'):
    x1, y1 = pt1
    x2, y2 = pt2
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    drawpoly(img, pts, color, thickness, style)