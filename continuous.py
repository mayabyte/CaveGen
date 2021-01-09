
from argparse import Namespace
import cv2
import numpy as np
import os
import glob
import sys
import time
import ast
import random

default_cave_order = "Emergence Cave,Emergence Cave,Hole of Beasts,Hole of Beasts,Hole of Beasts,Hole of Beasts,Hole of Beasts,White Flower Garden,White Flower Garden,White Flower Garden,White Flower Garden,White Flower Garden,Snagret Hole,Snagret Hole,Snagret Hole,Snagret Hole,Snagret Hole,Snagret Hole,Snagret Hole,Bulblax Kingdom,Bulblax Kingdom,Bulblax Kingdom,Bulblax Kingdom,Bulblax Kingdom,Bulblax Kingdom,Bulblax Kingdom,Subterranean Complex,Subterranean Complex,Subterranean Complex,Subterranean Complex,Subterranean Complex,Subterranean Complex,Subterranean Complex,Subterranean Complex,Frontier Cavern,Frontier Cavern,Frontier Cavern,Frontier Cavern,Frontier Cavern,Frontier Cavern,Frontier Cavern,Citadel of Spiders,Citadel of Spiders,Citadel of Spiders,Citadel of Spiders,Citadel of Spiders,Glutton's Kitchen,Glutton's Kitchen,Glutton's Kitchen,Glutton's Kitchen,Glutton's Kitchen,Glutton's Kitchen".split(",")
default_cave_index = 0

with open("continuous_config.txt", "r") as f:
    args = Namespace(**ast.literal_eval(f.read()))
print(args)

try:
    os.mkdir(args.templates)
except FileExistsError:
    pass

videoFile=args.camera
if videoFile == 'find':
    list_of_files = glob.glob(args.video_path + "*")
    videoFile = max(list_of_files, key=os.path.getctime)
    print("Using: %s" % videoFile)
cap = cv2.VideoCapture(videoFile)

if (cap.isOpened() == False): 
    print("Failure - error opening video stream")
    print("make sure virtual cam is setup correctly")
    sys.exit(0)

### generate template numbers

templates = []

if not args.generate_new_templates:
    for i in range(10):
        temp = cv2.imread(args.templates + str(i) + ".png",cv2.IMREAD_UNCHANGED)
        templates.append(temp)
    templates.append(cv2.imread(args.templates + "_.png",cv2.IMREAD_UNCHANGED))
        
### generate template letters

letters = {}
letters_height = {}
letters_yoff = {}
letters_width = {}
letters_xoff = {}

for l in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
    img = cv2.imread('files/letters/' + (l+l if l.isupper() else l) + ".png")
    img = cv2.resize(img, (int(img.shape[1]*args.letters_xscale), int(img.shape[0]*args.letters_yscale) ), interpolation=cv2.INTER_NEAREST)
    letters[l] = np.uint8(img)
    row_mean = letters[l].max(axis=2).max(axis=1)
    min_idx = 1000
    max_idx = 0
    for i in range(len(row_mean)):
        if row_mean[i] > 6:
            min_idx = min(min_idx,i)
            max_idx = max(max_idx,i)
    letters_height[l] = max_idx-min_idx+1
    letters_yoff[l] = min_idx
    col_mean = letters[l].max(axis=2).max(axis=0)
    min_idx = 1000
    max_idx = 0
    for i in range(len(col_mean)):
        if col_mean[i] > 6:
            min_idx = min(min_idx,i)
            max_idx = max(max_idx,i)
    letters_width[l] = max_idx-min_idx+1
    letters_xoff[l] = min_idx
    #print(l + " " + str(img.shape) + " h" + str(letters_height[l]) + " y" + str(letters_yoff[l]) + " w" + str(letters_width[l]) + " x" + str(letters_xoff[l]))

other_letters_w = {" ": args.space_mult, "'": args.apostrophe_mult}

### find and read the digits of a single frame

def read_digits_on_frame(image):

    if args.images:
        comp_img = np.zeros((11*args.height,5*args.width,3), np.uint8)
    output_digits = []
    
    for i in range(5):
        img = image[args.y:args.y+args.height, args.x+args.spacing*i:args.x+args.spacing*i+args.width, :]
        img = img.copy()
        #blur = cv2.GaussianBlur(img,(139,139),0) # this is too slow
        blur = np.zeros(img.shape, np.uint8)
        blur[:,:] = frame.mean(axis=0).mean(axis=0)
        diff = cv2.subtract(128 + cv2.subtract(img,blur),cv2.subtract(blur,img))
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        score = []
        #score_addn = [-0.02, 0.015, 0, 0.01, 0,  0, 0, 0.015, 0, 0,  0.07]
        score_addn = [0,0.01,0,0.01,0, 0,0,0,0,0, 0.03]
        for j in range(11):
            template = templates[j]
            res = cv2.matchTemplate(diff,template,cv2.TM_SQDIFF_NORMED)
            score.append((j,res.min(axis=0).min(axis=0) + score_addn[j]))

        score = sorted(score, key=lambda x: x[1])
        pred = score[0][0] if score[0][1] < 0.18 else 10

        if args.verbose:
            print(",".join(["%d %.3f" % x for x in score]))
        if args.images:
            for j in range(11):
                temp_height,temp_width = templates[j].shape[:2]
                temp_x = i*args.width+(args.width-temp_width)//2
                temp_y = j*args.height+(args.height-temp_height)//2
                comp_img[j*args.height:j*args.height+args.height, i*args.width:i*args.width+args.width, 0] = diff
                comp_img[j*args.height:j*args.height+args.height, i*args.width:i*args.width+args.width, 1] = (0 if pred==j else diff)
                comp_img[j*args.height:j*args.height+args.height, i*args.width:i*args.width+args.width, 2] = 128
                comp_img[temp_y:temp_y+temp_height, temp_x:temp_x+temp_width, 2] = templates[j]
        
        output_digits.append(pred)

    # sss = "files/digits6/" + str(count) + "-" + "".join([str(i) if i < 10 else '_' for i in output_digits]) + ".png"
    # print(sss)
    # cv2.imwrite(sss, image)

    print("digits " + "".join([str(i) if i < 10 else '_' for i in output_digits]), flush=True)
    if args.images:
        cv2.imshow('Digit', comp_img)
        cv2.waitKey(500)

### check for frames of the challenge mode result screen

# https://stackoverflow.com/questions/50899692/most-dominant-color-in-rgb-image-opencv-numpy-python
def bincount_app(a):
    a2D = a.reshape(-1,a.shape[-1])
    a2D = np.floor_divide(a2D,64)
    col_range = (4, 4, 4) # generically : a2D.max(0)+1
    a1D = np.ravel_multi_index(a2D.T, col_range)
    return np.unravel_index(np.bincount(a1D).argmax(), col_range)
    
def is_chresult_screen(frame):
    height,width = frame.shape[:2]
    x = width//8
    y = height//25
    window = frame[0:y, 3*x:5*x, :]
    b,g,r = window.mean(axis=0).mean(axis=0)
    #print("frame: %d %d %d" % (b,g,r))
    return abs(b-252) + abs(g-11) + abs(r-1) < 15 or abs(b-128) + abs(g-0) + abs(r-0) < 5
    # b,g,r = bincount_app(frame)
    # if args.verbose:
    # return b==3 and g==2 and r==2

def is_fadeout_screen(frame):
    average = frame.mean(axis=0).mean(axis=0)
    return average[0] < 5 and average[1] < 5 and average[2] < 5

def is_levelenter_screen(frame):
    height,width = frame.shape[:2]
    x = width
    y = height//20
    window1 = frame[0:4*y, 0:x, :]
    window2 = frame[4*y:8*y, 0:x, :]
    window3 = frame[8*y:10*y, 0:x, :]
    window4 = frame[10*y:13*y, x//4:3*x//4, :]
    window5 = frame[13*y:height, 0:x, :]
    average1 = window1.mean(axis=0).mean(axis=0)
    average2 = window2.mean(axis=0).mean(axis=0)
    average3 = window3.mean(axis=0).mean(axis=0)
    average4 = window4.mean(axis=0).mean(axis=0)
    average5 = window5.mean(axis=0).mean(axis=0)
    # print()
    # print(average1)
    # print(average2)
    # print(average3)
    # print(average4)
    # print(average5)
    # frame[4*y,:,:] = 255
    # frame[8*y,:,:] = 255
    # frame[10*y,:,:] = 255
    # frame[13*y,:,:] = 255

    # f = 7 jack
    # if  average1[0] < f and average1[1] < f and average1[2] < f and \
    #     average2[0] < f and average2[1] < f and average2[2] < f and \
    #     average3[0] < f and average3[1] < f and average3[2] < f and \
    #     average4[0] < f and average4[1] < f and average4[2] < f and \
    #     average5[0] < f and average5[1] < f and average5[2] < f and abs(average4[2]-average5[2])<2:
    #     return 'fadeout'
    # if  average1[0] < f and average1[1] < f and average1[2] < f and \
    #     average2[0] < 50 and average2[1] < 50 and average2[2] > 15 and average2[2] < 70 and abs(average2[0] - average2[2]) > 10 and \
    #     average3[0] < f and average3[1] < f and average3[2] < f and \
    #     average4[0] > f and average4[1] > f and average4[2] > f and \
    #     average4[0] < 40 and average4[1] < 40 and average4[2] < 40 and \
    #     average5[0] < f and average5[1] < f+1 and average5[2] < f+5:
    #     return 'chenter'
    # if  average1[0] < 25 and average1[1] < 25 and average1[2] < 25 and \
    #     average2[0] < 40 and average2[1] < 40 and average2[2] < 40 and abs(average2[0] - average2[2]) < 6 and abs(average2[0] - average2[1]) < 6 and \
    #     average3[0] < 25 and average3[1] < 25 and average3[2] < 25 and \
    #     average4[0] > f and average4[1] > f and average4[2] > f and \
    #     average4[0] < 40 and average4[1] < 40 and average4[2] < 40 and \
    #     average5[0] < f and average5[1] < f+1 and average5[2] < f+5:
    #     return 'storyenter'
    f = args.fadeout_frame_intensity # ice
    if  average1[0] < f and average1[1] < f and average1[2] < f and \
        average2[0] < f and average2[1] < f and average2[2] < f and \
        average3[0] < f and average3[1] < f and average3[2] < f and \
        average4[0] < f and average4[1] < f and average4[2] < f and \
        average5[0] < f and average5[1] < f and average5[2] < f and abs(average4[2]-average5[2])<2:
        return 'fadeout'
    if  average1[0] < f and average1[1] < f and average1[2] < f and \
        average2[0] < f+45 and average2[1] < f+45 and average2[2] > f+10 and average2[2] < f+65 and abs(average2[0] - average2[2]) > f+5 and \
        average3[0] < f and average3[1] < f and average3[2] < f and \
        average4[0] > f and average4[1] > f and average4[2] > f and \
        average4[0] < f+35 and average4[1] < f+35 and average4[2] < f+35 and \
        average5[0] < f and average5[1] < f+1 and average5[2] < f+5:
        return 'chenter'
    if  average1[0] < f+20 and average1[1] < f+20 and average1[2] < f+20 and \
        average2[0] < f+40 and average2[1] < f+40 and average2[2] < f+40 and abs(average2[0] - average2[2]) < 6 and abs(average2[0] - average2[1]) < 8 and \
        average3[0] < f+25 and average3[1] < f+25 and average3[2] < f+25 and \
        (average4[0] > f or average4[1] > f or average4[2] > f) and \
        average4[0] < f+40 and average4[1] < f+40 and average4[2] < f+40 and \
        average5[0] < f+5 and average5[1] < f+5 and average5[2] < f+5:
        return 'storyenter'

    
    return None

def generate_new_templates(image):

    copy = image.copy()
    
    for i in range(5):
        img = image[args.y:args.y+args.height, args.x+args.spacing*i:args.x+args.spacing*i+args.width, :]
        img = img.copy()
        #blur = cv2.GaussianBlur(img,(139,139),0)
        blur = np.zeros(img.shape, np.uint8)
        blur[:,:] = frame.mean(axis=0).mean(axis=0)
        diff = cv2.subtract(128 + cv2.subtract(img,blur),cv2.subtract(blur,img))
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        cv2.imwrite(args.templates + str(count) + "-" + str(i) + ".png", diff)

        if i % 2 == 0:
            copy[args.y:args.y+args.height, args.x+args.spacing*i:args.x+args.spacing*i+args.width, 2] = 200
        else:
            copy[args.y:args.y+args.height, args.x+args.spacing*i:args.x+args.spacing*i+args.width, 1] = 200
    
    cv2.imshow('Digit', copy)
    cv2.waitKey(args.template_wait)

    with open("files/continuous_config.txt", "r") as f:
        updated = Namespace(**ast.literal_eval(f.read()))
        args.x = updated.x
        args.y = updated.y
        args.spacing = updated.spacing
        args.width = updated.width
        args.height = updated.height
    
falling_img = None
union_img = None
frames_since_first_story = 10000
frames_since_last_story = 10000
story_frames = []
story_frames_processed = False
num_letters_info = 0

def process_story_frames_name_known():
    print("processing story frames with name known")

    # find the cave name
    cave_name = ""

    global default_cave_index
    global num_letters_info
    with open("files/cave_name.txt") as f:
        cave_name = f.readline().strip()
    if cave_name == "":
        cave_name = default_cave_order[default_cave_index]
        default_cave_index += 1
    else:
        with open('files/cave_name.txt', 'r') as fin:
            data = fin.read().splitlines(True)
        with open('files/cave_name.txt', 'w') as fout:
            fout.writelines(data[1:])
    #print("cave=" + cave_name)

    height,width = story_frames[0].shape[:2]

    #print(height)
    #print(width)

    # compute the average image after the letters have stopped moving
    if args.images:
        num_avg = 25
        sum_img = story_frames[0].copy()
        sum_img[:,:,:] = 0
        for frame in story_frames[-num_avg:]:
            sum_img = sum_img + frame / num_avg
        _,avg_thresh_img = cv2.threshold(sum_img,75,255,cv2.THRESH_BINARY)

    # important params
    max_row_for_falling = int(height*args.max_for_falling)

    # find the expected with of the image
    temp_w = 0
    temp_h = 0
    for l in cave_name:
        if l in letters:
            img = letters[l]
            temp_h = max(temp_h, img.shape[0])
            temp_w += img.shape[1]
        else:
            temp_w += letters['l'].shape[1] * other_letters_w[l]

    # compute the letters postions, scrunching if necesary
    xs0 = []
    xs1 = []
    x_off = int(width/2 - temp_w/2 + args.letters_xoffset)
    y_off = int(height*args.letters_yoffset)
    x_scrunch = 1
    x_scrunch_limit = args.x_scrunch_limit
    if temp_w > x_scrunch_limit * width:
        x_scrunch = x_scrunch_limit * width/temp_w
        x_off = int(width * (1-x_scrunch_limit)//2)+args.letters_xoffset
        #print("x scr " + str(x_scrunch))
    if args.images:
        sum_img[:,:,0]=0
        sum_img[:,int(width*(1-x_scrunch_limit)//2)+args.letters_xoffset,0] = 255
        sum_img[:,int(width-width*(1-x_scrunch_limit)//2)+args.letters_xoffset,0] = 255
    for l in cave_name:
        xs0.append(int(x_off))
        if l in letters:
            if args.images:
                img = letters[l].copy()
                img[:,:,1:2] = 0
                img = cv2.resize(img, (int(img.shape[1]*x_scrunch), img.shape[0] ), interpolation=cv2.INTER_NEAREST)
                sum_img[y_off:y_off+img.shape[0], int(x_off):int(x_off)+img.shape[1], :] = sum_img[y_off:y_off+img.shape[0], int(x_off):int(x_off)+img.shape[1], :] + img
            x_off += letters[l].shape[1]*x_scrunch
        else:
            x_off += letters['l'].shape[1] * other_letters_w[l] * x_scrunch
        xs1.append(int(x_off))
    
    # determine vertical cutoffs to use
    xs0_use = []
    xs1_use = []
    spacing_needed = int(width * 0.008)
    #print("sp " + str(spacing_needed))
    for i,l in enumerate(cave_name):
        if l not in letters:
            xs0_use.append(xs0[i])
            xs1_use.append(xs1[i])
            continue
        x0 = max(xs0[i]+1, xs1[i-1]-int((letters[cave_name[i-1]].shape[1]-letters_xoff[cave_name[i-1]]-letters_width[cave_name[i-1]])*x_scrunch)+spacing_needed if i>0 and cave_name[i-1] in letters else 0)
        x1 = min(xs1[i]-1, xs0[i+1]+int(letters_xoff[cave_name[i+1]]*x_scrunch)-spacing_needed if i+1<len(xs0) and cave_name[i+1] in letters else width)
        if i+1<len(xs0) and cave_name[i+1]=="'":
            x1 -= spacing_needed
        if x0 + 4 >= x1:
            diff = (x0 + 4 - x1) // 2
            x0 -= diff
            x1 += diff
        xs0_use.append(x0)
        xs1_use.append(x1)
        if args.images:
            sum_img[0:height//2,x0,0] = 255
            sum_img[0:height//2,x1,0] = 255

            #falling_img[0:height//2,x0,0] = 255
            #falling_img[0:height//2,x1,0] = 255
            #if l in letters:
            #    sum_img[y_off+letters_yoff[l]:y_off+letters_yoff[l]+letters_height[l],x0+letters_xoff[l]:x0+letters_xoff[l]+letters_width[l],1]=155
    

    
    # for each frame with a falling letter, compute the location of the falling letter
    locs = np.zeros((len(cave_name), 45))
    for story_frame_count,frame in enumerate(story_frames[0:45]):

        #print("storyenter " + str(story_frame_count), flush=True)
        #_,img = cv2.threshold(frame,13,255,cv2.THRESH_BINARY) # may need to change this for wii
        for i,l in enumerate(cave_name):
            if l not in letters: continue
            #print(f"{l} {xs0_use[i]} {xs1_use[i]} {img.shape}")
            section_img = frame[0:max_row_for_falling,xs0_use[i]:xs1_use[i],:]
            row_means = section_img.max(axis=2).max(axis=1)
            #print(row_means)
            last_nonzero = -1
            num_rows_with_stuff = 0
            for j,r in enumerate(row_means):
                if r > args.letter_intensity_thresh:
                    num_rows_with_stuff += 1
                    last_nonzero = j
            if last_nonzero >= 4 and last_nonzero < max_row_for_falling-1 and num_rows_with_stuff > min(last_nonzero*.75, letters_height[l]*.75):
                locs[i][story_frame_count] = last_nonzero 
                #print(str(i//2) + " " + str(last_nonzero))
                #info_string.append(str(i//2+spaces_between[i//2])+","+str(last_nonzero)+",")
                #union_img[last_nonzero,xs0_use[i]:xs1_use[i],:]=0
                #union_img[last_nonzero,xs0_use[i]:xs1_use[i],2]=255
                if args.images:
                    falling_img[last_nonzero,xs0_use[i]:xs1_use[i],:]=0
                    falling_img[last_nonzero,xs0_use[i]:xs1_use[i],2]=255
                    #img[last_nonzero,whitespace[i]:whitespace[i+1],:]=0
                    #img[last_nonzero,whitespace[i]:whitespace[i+1],2]=255
                    if num_letters_info == 1:
                        ims = frame[0:max_row_for_falling,xs0_use[i]:xs1_use[i],2]
                        imgs = ims.copy()
                        imgs[last_nonzero,:] = 255
                        cv2.imwrite("im/" + str(i) + str(l) + str(story_frame_count) + ".png", imgs)
                
        if args.images:
            pass
            #cv2.imwrite("im/" + str(count) + "s" + str(story_frame_count) + ".png", img)
        #info_string.append(";")

    if args.verbose:
        for x in locs:
            print(x)

    # try to do some sanity checking on the output...
    # each non space char should have 3-6 entries, all consecutive, and the diffs should be around a certain value
    # otherwise, zero out
    num_bad_char = 0
    for i,l in enumerate(cave_name):
        nonzero = []
        nonzero_idx = []
        for j,y in enumerate(locs[i]):
            if y>0:
                nonzero.append(y)
                nonzero_idx.append(j)
        if len(nonzero) == 0: continue
        good = len(nonzero) >= 3 and len(nonzero) <= 6 and nonzero_idx[-1]-nonzero_idx[0] == len(nonzero)-1
        for j in range(len(nonzero)-1):
            diff = nonzero[j+1]-nonzero[j]
            if diff/height < 10/720 or diff/height > 35/720:
                good=False
        if not good:
            num_bad_char += 1
            locs[i,:] = 0

    # if still good, create the info string. If bad but still seems like a cave entry, write out an empty infostring
    # otherwise, do nothing (this case shouldn't be hit hopefully)

    if num_bad_char > len(cave_name)/2:
        print("too many bad chars")
    elif num_bad_char > 2:
        num_letters_info += 1
        print("lettersinfo,,100,0;;;", flush=True)
    else:
        num_letters_info += 1
        # compute & write out the info string...
        info_string = []
        offset_info = []
        for i,l in enumerate(cave_name):
            if l in letters:
                offset_info.append(str(letters[l].shape[0]-letters_height[l]-letters_yoff[l]))
            else:
                offset_info.append(str(-1))

        for j in range(len(locs[0])):
            s = ""
            for i in range(len(locs)):
                if locs[i][j] > 0:
                    s += str(i) + "," + str(int(locs[i][j])) + ","
            s += ";"
            info_string.append(s)

        print("lettersinfo," + cave_name.replace(" ","_") + "," + str(height) 
            + "," + str(len(cave_name)) + "," + ",".join(offset_info) + ";" + "".join(info_string), flush=True)    
    
    if args.images:
        min_row_for_columns = 26*height//100
        max_row_for_columns = 35*height//100
        sum_img[min_row_for_columns,:,:] = 255
        sum_img[max_row_for_columns,:,:] = 255
        # union_img[max_row_for_falling,:,:] = 0 
        # union_img[max_row_for_falling,:,0] = 155
        falling_img[max_row_for_falling,:,:] = 0 
        falling_img[max_row_for_falling,:,0] = 155
    #     for x in whitespace:
    #         avg_thresh_img[0:max_row_for_columns,x,:] = 0
    #         avg_thresh_img[0:max_row_for_columns,x,2] = 255
    #         union_img[0:max_row_for_columns,x,:] = 0
    #         union_img[0:max_row_for_columns,x,2] = 255
    #         falling_img[0:max_row_for_columns,x,:] = 0
    #         falling_img[0:max_row_for_columns,x,2] = 255

        cv2.imwrite("im/" + str(count) + "!avg" + ".png", sum_img)
        #cv2.imwrite("im/" + str(count) + "!avg_th" + ".png", avg_thresh_img)
        #cv2.imwrite("im/" + str(count) + "!union" + ".png", union_img)
        cv2.imwrite("im/" + str(count) + "!union_p" + ".png", falling_img)


def random_colorize(img):
    ret = img.copy()
    ret[:,:,0] = img[:,:,2]*(random.randint(100,255)/255)
    ret[:,:,1] = img[:,:,2]*(random.randint(100,255)/255)
    ret[:,:,2] = img[:,:,2]*(random.randint(100,255)/255)
    return ret

    
### watch the video, find frames of the challenge mode result screen, and read the digits  
skip = 0
count = 0
last_frame_was_digit = False

frame_for_save_count = 0
frames_to_output_anyways = 0
save_to_im_save = False

# while True:
#     frame_for_save_count += 1
#     frame = cv2.imread('im_save/' + str(frame_for_save_count) + '.png', cv2.IMREAD_COLOR)
#     ret = True

while(cap.isOpened()):
    ret, frame = cap.read()

    count += 1
    frames_since_first_story += 1
    frames_since_last_story += 1
    
    if not ret:
        break
    if skip > 0:
        skip -= 1
        continue

    #if count < 8*60*30:
    #    continue
 
    height,width = frame.shape[:2]
    if count == 1:
       print(f"height {height} width {width}")
    #frame = cv2.resize(frame, (853,480), interpolation=cv2.INTER_NEAREST)
    if args.crop:
        frame = frame[args.crop_y1:args.crop_y2,args.crop_x1:args.crop_x2,:]
    
    frame_type = is_levelenter_screen(frame)
    
    if frame_type == 'fadeout':
        print("fadeout " + str(count),flush=True)
    elif frame_type == 'chenter':
        print("levelenter", flush=True)
    elif frame_type == 'storyenter':
        print("storyenter " + str(count), flush=True)
        img = frame.copy()
        story_frames.append(img)
        _,img = cv2.threshold(img,args.letter_intensity_thresh,255,cv2.THRESH_BINARY)
        # Creating kernel 
        kernel = np.ones((3, 3), np.uint8) 
        img = cv2.erode(img, kernel) 
        if frames_since_last_story > 10:
            falling_img = np.zeros(frame.shape)
            union_img = np.zeros(frame.shape)
            frames_since_first_story = 0
            story_frames = []
            story_frames.append(img)
            story_frames_processed = False
        if frames_since_first_story <= 45:
            if args.images:
                falling_img = falling_img + random_colorize(img)/4
            #union_img = union_img + img/5
        frames_since_last_story = 0

        frames_to_output_anyways = 40

        if frames_since_first_story >= (60 if not args.images else 75) and len(story_frames) >= (60 if not args.images else 75):
            if not story_frames_processed:
                story_frames_processed = True
                process_story_frames_name_known()

    elif is_chresult_screen(frame):
        if args.generate_new_templates:
            generate_new_templates(frame)
        else:
            read_digits_on_frame(frame)
        last_frame_was_digit = True
    else:
        if last_frame_was_digit:
            print("donedigit",flush=True)
        else:
            skip = 10
        last_frame_was_digit = False

    if frames_to_output_anyways > 0 and save_to_im_save and args.images:
        frames_to_output_anyways -= 1
        frame_for_save_count += 1
        cv2.imwrite("im_save/" + str(frame_for_save_count) + ".png", frame)
        if frames_to_output_anyways == 0:
            for jjj in range(40):
                jjjj = frame.copy()
                jjjj[:,:,:]=0
                frame_for_save_count += 1
                cv2.imwrite("im_save/" + str(frame_for_save_count) + ".png", jjjj)

    
    if args.playback:
        cv2.imshow('Frame',frame)
        key_press = cv2.waitKey(1)
        if key_press & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("exit")

