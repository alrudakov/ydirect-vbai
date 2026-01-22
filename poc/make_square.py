"""
Превращает вертикальную картинку в квадратную с тёмным фоном
"""
from PIL import Image

# Пути
input_path = r'C:\Users\fatal\Desktop\Projects\ydirect-vbai\Creative\IT\DevOps1\1.jpg'
output_path = r'C:\Users\fatal\Desktop\Projects\ydirect-vbai\Creative\IT\DevOps1\2.jpg'

# Загружаем
img = Image.open(input_path)
w, h = img.size
print(f'Исходный размер: {w}x{h}')

# Размер квадрата = большая сторона
size = max(w, h)

# Тёмный фон (как терминал)
bg_color = (18, 18, 24)
square = Image.new('RGB', (size, size), bg_color)

# Вставляем по центру
x_offset = (size - w) // 2
y_offset = (size - h) // 2
square.paste(img, (x_offset, y_offset))

# Сохраняем
square.save(output_path, 'JPEG', quality=95)

print(f'✅ Сохранено: {output_path}')
print(f'Новый размер: {size}x{size} (1:1)')

