from rich.console import Console

file_name = "pepapig-sigma.gif"
with open(file_name,"rb") as f:
    data = f.read()
    f.close()

wh = int.from_bytes(data[6:8], "little")
ht = int.from_bytes(data[8:10], "little")
packed = data[10]
# пока считаем что глобальная палитра есть
# здесь создаем глобальную палитру цветов в нашей гивке
count_color = 2 ** ((packed & 0b00000111) + 1)
global_color_table_size = count_color * 3
start_palette = 13
palette = []
for i in range(count_color):
    r = data[start_palette + i * 3]
    g = data[start_palette + i * 3 + 1]
    b = data[start_palette + i * 3 + 2]
    palette.append( (r, g, b) )

# здесь мы распарсили заголовок и глобальную палитру и переходим к парсингу блоков (кадров по сути гивки)
offset = start_palette + global_color_table_size

# тут стоит прописать принты и вывести основной блок информации о гивке (это вообще хз что хотят тут увидеть)


while data[offset] != 0x3B:
    # здесь чекаем рабочую инфу кадра (конкретно какой цвет прозрачный если он есть)
    # мб еще от сюда можно взять с какой частотой показывать кадр, но пока ваще пофиг
    if data[offset] == 0x21:
        label = data[offset + 1]
        if label == 0xF9:
            block_size = data[offset + 2]
            packed = data[offset + 3]
            transparency_flag = (packed & 0b00000001)
            if transparency_flag:
                transparency_index = data[offset + 6]
            else:
                transparency_index = None
            offset += 2 + block_size + 1
        else:
            offset += 2
            while True:
                sub_block_size = data[offset]
                if sub_block_size == 0:
                    offset += 1
                    break
                offset += 1 + sub_block_size
    # здесь парсим конкретный кадр
    # сделала пока только считывание локальной палитры если она есть 
    elif data[offset] == 0x2C:
        image_left = int.from_bytes(data[offset + 1:offset + 3], "little")
        image_top = int.from_bytes(data[offset + 3:offset + 5], "little")
        image_width = int.from_bytes(data[offset + 5:offset + 7], "little")
        image_height = int.from_bytes(data[offset + 7:offset + 9], "little")

        packed = data[offset + 9]
        local_color_table_flag = (packed & 0b10000000) >> 7

        local_color_table_size = 0
        local_palette = []
        if local_color_table_flag:
            count_color = 2 ** ((packed & 0b00000111) + 1)
            local_color_table_size = count_color * 3
            for i in range(count_color):
                r = data[offset + 10 + i * 3]
                g = data[offset + 10 + i * 3 + 1]
                b = data[offset + 10 + i * 3 + 2]
                local_palette.append( (r, g, b) )
        else:
            local_palette = palette
        

        # здесь собираем сжатые данные кадра
        lzw_min_code_size = data[offset + 10]
        offset += 11 + local_color_table_size

        compressed_data = bytearray()
        while True:
            sub_block_size = data[offset]
            offset += 1
            if sub_block_size == 0:
                break
            compressed_data += data[offset: offset + sub_block_size]
            offset += sub_block_size
        # и нужно их распарсить и превратить в массив пикселей или тип того
        # удобно если в массив пикселей так как метод отрисовки (что находится ниже) принимает именно такой формат
        # надо сделать какой то LZW декодер но чет лень пока

        # ну и все, если мы получим массив пикселей то можно отрисовать кадр
        # print_frame(image_width, image_height, local_palette, transparency_index, pixels)

        #ну и он будет так делать в цикле так что по сути анимация 



def print_frame(wh, ht, palette, transparency, pixels):
    console = Console()
    
    light_color = (200, 200, 200)
    dark_color  = (120, 120, 120)

    for y in range(ht):
        row = ""
        for x in range(wh):
            idx = pixels[x, y]

            if transparency is not None and idx == transparency:
                color = light_color if (x + y) % 2 == 0 else dark_color
                r, g, b = color
            else:
                r, g, b = palette[idx]
            row += f"[on rgb({r},{g},{b})] [/]"
        console.print(row)

