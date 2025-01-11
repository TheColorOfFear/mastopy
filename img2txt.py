from PIL import Image
import os
if __name__ == '__main__':
    import sys

e = "\033["
fc = [e+"97m",e+"90m",e+"30m"]
bc = [e+"107m",e+"100m",e+"40m"]
c = e+"0m"
chars= ["@", "J", "D", "%", "*", "P", "+", "Y", "$", ",", "."]
#chars= ["█", "█", "█", "▓", "▓", "▒", "▒", "▒", " ", " ", " "]
#chars= ["█", "▇", "▆", "▅", "▄", "▃", "▂", "▁", " ", " ", " "]
#chars= [fc[0]+"█"+c, bc[1]+fc[0]+"▓"+c, bc[1]+fc[0]+"▒"+c, bc[0]+fc[1]+"░"+c, bc[1]+fc[0]+"░"+c, bc[0]+fc[1]+"▒"+c, bc[0]+fc[1]+"▓"+c, bc[0]+fc[1]+"█"+c, " "+c, " "+c]
#chars= [" "+c, bc[0]+fc[1]+"█"+c, bc[0]+fc[1]+"▓"+c, bc[0]+fc[1]+"▒"+c, bc[1]+fc[0]+"░"+c, bc[0]+fc[1]+"░"+c, bc[1]+fc[0]+"▒"+c, bc[1]+fc[0]+"▓"+c, fc[0]+"█"+c, fc[0]+"█"+c]
fourths= [" ","▘","▝","▀","▖","▌","▞","▛","▗","▚","▐","▜","▄","▙","▟","█"]

def get_fourth(pixels, width, place):
    thisone = str(pixels[place + width + 1]//255)
    thisone += str(pixels[place + width]//255)
    thisone += str(pixels[place + 1]//255)
    thisone += str(pixels[place]//255)
    indice = int(thisone,2)
    return fourths[indice]


def open_img(imgName, wid=80, stretch=0.55, hstretch=1):
    img = Image.open(imgName, mode='r')
    width, height = img.size
    if wid != "original":
        newwid = wid
    else:
        newwid = width
    aspect_ratio = height/width
    new_height = aspect_ratio * newwid * stretch * hstretch
    img = img.resize((newwid * hstretch, int(new_height)), resample=Image.BILINEAR)
    img = img.convert(mode="RGB")
    pixels = img.getdata()
    return img, newwid

def print_img_bw(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid)
    pixels = img.convert(mode="L").getdata()
    ascii_image = "\n"
    for i in range(len(pixels)//newwid):
        for j in range(newwid):
            try:
                ascii_image += chars[min( (pixels[j + (i*newwid)]//25),(len(chars) - 1))]
            except:
                raise
                print(pixels[j + (i*newwid)]//25)
        ascii_image += "\n"
    '''
    new_pixels = [chars[pixel//25] for pixel in pixels]
    new_pixels = ''.join(new_pixels)
    
    # split string of chars into multiple strings of length equal to new width and create a list
    new_pixels_count = len(new_pixels)
    ascii_image = [new_pixels[index:index + wid] for index in range(0, new_pixels_count, wid)]
    ascii_image = "\n".join(ascii_image)
    '''
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_ascii_256_ld(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid)
    pixels = img.getdata()
    pixels_bw = img.convert(mode="L").getdata()
    ascii_image = "\n"
    for i in range(len(pixels)//newwid):
        for j in range(newwid):
            try:
                ascii_image += e + "38;5;"
                r = ((pixels[j + (i*newwid)][0]) * 5) // 256
                g = ((pixels[j + (i*newwid)][1]) * 5) // 256
                b = ((pixels[j + (i*newwid)][2]) * 5) // 256
                ascii_image += str( ( (b ) + (g * 6) + (r * 36) ) + 16) + "m"
                ascii_image += chars[min( (pixels_bw[j + (i*newwid)]//25),(len(chars) - 1))]
                ascii_image += c
            except:
                raise
                print(pixels[j + (i*newwid)]//25)
        ascii_image += "\n"
    '''
    new_pixels = [chars[pixel//25] for pixel in pixels]
    new_pixels = ''.join(new_pixels)
    
    # split string of chars into multiple strings of length equal to new width and create a list
    new_pixels_count = len(new_pixels)
    ascii_image = [new_pixels[index:index + wid] for index in range(0, new_pixels_count, wid)]
    ascii_image = "\n".join(ascii_image)
    '''
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_ld(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid)
    pixels = img.getdata()
    ascii_image = "\n"
    for i in range(len(pixels)//newwid):
        for j in range(newwid):
            ascii_image += e + "38;2;"
            ascii_image += str(pixels[j + (i*newwid)][0]) + ";"
            ascii_image += str(pixels[j + (i*newwid)][1]) + ";"
            ascii_image += str(pixels[j + (i*newwid)][2]) + "m"
            ascii_image += "█"
        ascii_image += "\n"
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_col(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid, 1)
    pixels = img.getdata()
    ascii_image = "\n"
    for i in range(0,len(pixels)//(newwid),2):
        for j in range(newwid):
            try:
                ascii_image += e + "38;2;"
                ascii_image += str(pixels[j + (i*newwid)][0]) + ";"
                ascii_image += str(pixels[j + (i*newwid)][1]) + ";"
                ascii_image += str(pixels[j + (i*newwid)][2]) + "m"
                ascii_image += e + "48;2;"
                ascii_image += str(pixels[j + ((i + 1)*newwid)][0]) + ";"
                ascii_image += str(pixels[j + ((i + 1)*newwid)][1]) + ";"
                ascii_image += str(pixels[j + ((i + 1)*newwid)][2]) + "m"
                ascii_image += "▀" + c
            except IndexError:
                pass
        ascii_image += "\n"
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_256_ld(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid, 1)
    pixels = img.getdata()
    ascii_image = "\n"
    for i in range(0,len(pixels)//(newwid), 2):
        for j in range(newwid):
            try:
                ascii_image += e + "38;5;"
                r = ((pixels[j + (i*newwid)][0]) * 5) // 256
                g = ((pixels[j + (i*newwid)][1]) * 5) // 256
                b = ((pixels[j + (i*newwid)][2]) * 5) // 256
                ascii_image += str( ( (b ) + (g * 6) + (r * 36) ) + 16) + "m"
                ascii_image += "█" + c
            except IndexError:
                pass
        ascii_image += "\n"
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_256(imgName, wid=80, ret=False):
    img, newwid = open_img(imgName, wid, 1)
    pixels = img.getdata()
    ascii_image = "\n"
    for i in range(0,len(pixels)//(newwid), 2):
        for j in range(newwid):
            try:
                ascii_image += e + "38;5;"
                r = ((pixels[j + (i*newwid)][0]) * 5) // 256
                g = ((pixels[j + (i*newwid)][1]) * 5) // 256
                b = ((pixels[j + (i*newwid)][2]) * 5) // 256
                ascii_image += str( ( (b ) + (g * 6) + (r * 36) ) + 16) + "m"
                ascii_image += e + "48;5;"
                r = ((pixels[j + ((i + 1)*newwid)][0]) * 5) // 256
                g = ((pixels[j + ((i + 1)*newwid)][1]) * 5) // 256
                b = ((pixels[j + ((i + 1)*newwid)][2]) * 5) // 256
                ascii_image += str( ( (b ) + (g * 6) + (r * 36) ) + 16) + "m"
                ascii_image += "▀" + c
            except IndexError:
                pass
        ascii_image += "\n"
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img_256_vh(imgName, wid=80, ret=False):
    def getcol_index(colour, indice):
        r = ((colours[indice][0]) * 5) // 256
        g = ((colours[indice][1]) * 5) // 256
        b = ((colours[indice][2]) * 5) // 256
        return r,g,b
    img, newwid = open_img(imgName, wid, hstretch = 2)
    pixels = img.convert(mode="1", dither=None).getdata()
    colours = img.getdata()
    ascii_image = "\n"
    for i in range(0,len(pixels)//(newwid * 2), 2):
        for j in range(0,newwid*2,2):
            try:
                ind = j + (i*newwid*2)
                ind_tl = ind
                ind_tr = ind + 1
                ind_bl = ind + newwid*2
                ind_br = ind - newwid*2 + 1
                
                fourth = get_fourth(pixels, newwid * 2, ind)
                fourth_index = fourths.index(fourth)
                fourth_bin = str(bin(fourth_index))[2:].zfill(4)
                
                tlcol = getcol_index(colours, ind_tl)
                trcol = getcol_index(colours, ind_tr)
                blcol = getcol_index(colours, ind_bl)
                brcol = getcol_index(colours, ind_br)
                
                cols = [brcol, blcol, trcol, tlcol]
                
                bg_r = 0
                bg_g = 0
                bg_b = 0
                bg_div = 0
                for k in range(4):
                    if fourth_bin[k] == "0":
                        bg_r += cols[k][0]
                        bg_g += cols[k][1]
                        bg_b += cols[k][2]
                        bg_div += 1
                if bg_div == 0:
                    bg_div = 1
                bg_r = bg_r // bg_div
                bg_g = bg_g // bg_div
                bg_b = bg_b // bg_div
                ascii_image += e + "48;5;" #background
                ascii_image += str( ( (bg_b ) + (bg_g * 6) + (bg_r * 36) ) + 16) + "m"
                '''
                fg_r = 0
                fg_g = 0
                fg_b = 0
                fg_div = 0
                for k in range(4):
                    if fourth_bin[k] == "1":
                        fg_r += cols[k][0]
                        fg_g += cols[k][1]
                        fg_b += cols[k][2]
                        fg_div += 1
                        print(cols[k],k)
                if fg_div == 0:
                    fg_div = 1
                print("---", fg_div)
                fg_r = fg_r // fg_div
                fg_g = fg_g // fg_div
                fg_b = fg_b // fg_div
                print((fg_r,fg_g,fg_b))
                ascii_image += e + "38;5;" #foreground
                ascii_image += str( ( (fg_b ) + (fg_g * 6) + (fg_r * 36) ) + 16) + "m"
                '''
                ascii_image += e+"97m" + fourth + c
            except IndexError:
                pass
        ascii_image += "\n"
    if ret:
        return ascii_image
    else:
        print(ascii_image)
        return None

def print_img(imgName, printType="colour", imgres="high", wid=80, ret=False):
    if wid == "max":
        wid = os.get_terminal_size()[0]
    elif wid == "original":
        wid = "original"
    else:
        wid = int(wid)
    if printType.lower() == "colour":
        if imgres.lower() == "high":
            out = print_img_col(imgName, wid, ret)
        else:
            out = print_img_ld(imgName, wid, ret)
    elif printType.lower() == "256":
        if imgres.lower() == "high":
            out = print_img_256(imgName, wid, ret)
        else:
            out = print_img_256_ld(imgName, wid, ret)
    elif printType.lower() == "bw":
        out = print_img_bw(imgName, wid, ret)
    elif printType.lower() == "ascii_colour":
        out = print_img_ascii_256_ld(imgName, wid, ret)
    elif printType.lower() == "test":
        out = print_img_256_vh(imgName, wid, ret)
    else:
        out = print_img_256_ld(imgName, wid, ret)
    return out

if __name__ == '__main__':
    print_type = "256"
    img_res = "high"
    img_width = "max"
    if len(sys.argv) > 1:
        img_name = sys.argv[1]
        if len(sys.argv) > 2:
            print_type = sys.argv[2]
            if len(sys.argv) > 3:
                img_res = sys.argv[3]
                if len(sys.argv) > 4:
                    img_width = sys.argv[4]
        print_img(img_name, print_type, img_res, img_width)
    else:
        #img_name = input("file name? : ")
        print("usage: [program] [file] [type] [res] [width]")
