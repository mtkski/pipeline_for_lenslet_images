from PIL import Image, ImageDraw
import numpy as np
import math
import xml.etree.ElementTree as ET
import sys
import argparse

from matplotlib import pyplot as plt
from scipy.ndimage import gaussian_filter
from skimage.io import imsave
from config_maker import get_config_dict # préciser où est config_maker.py

def xml_reader(calibFile):
    file = ET.parse(calibFile)
    root = file.getroot()

    for offset in root.findall('offset'):
        offset_x = offset.find('x').text
        offset_y = offset.find('y').text
    offset = np.array([offset_x, offset_y], dtype=float)
    print(f'offset_x: {offset_x}, offset_y: {offset_y}')

    lens = float(root.find('diameter').text)

    alpha = float(root.find('rotation').text)

    for base in root.findall('lens_base_y'):
        Lens_base_Yx = float(base.find('x').text)
        Lens_base_Yy = float(base.find('y').text)


    return offset, lens, alpha, Lens_base_Yx, Lens_base_Yy

#Used for debug
def colorPatch(cx, cy, rad, col, img):
    for x in range(int(cx-rad), int(cx + rad)+1):
        for y in range (int(cy-rad), int(cy+rad)+1):
            img[x,y] = col
    img[cx,cy] = (col[0]-50,col[1]-50,col[2]-50)

#Used previously
def distFromCenterBool(rad):

    Y,X = np.ogrid[:2*rad+1,:2*rad+1]
    dist_from_center = np.sqrt((X-(rad))**2 + (Y-(rad))**2)
    patch_mask = np.zeros((2*rad+1, 2*rad+1))

    patch_mask[dist_from_center <= rad] = 255

    return patch_mask

#Used previously
def distFromCenterXringYborder(rad,ring, border):
    effective_rad = rad + ring*border

    Y,X = np.ogrid[:2*effective_rad+1,:2*effective_rad+1]
    dist_from_center = np.sqrt((X - effective_rad) ** 2 + (Y - effective_rad) ** 2)
    patch_mask = np.zeros((2 * effective_rad + 1, 2 * effective_rad + 1))

    val = np.arange(0, 255 + 1, 255 / (ring + 1))
    val = val[1:]
    r = np.arange(rad, effective_rad + 1, border)
    r = r[::-1]

    for i in range(len(r)):
        patch_mask[dist_from_center < r[i]] = int(val[i])

    return patch_mask

def distFromCenterXringYborderLogScale(rad,ring, border):
    effective_rad = rad + ring*border

    Y,X = np.ogrid[:2*effective_rad+1,:2*effective_rad+1]
    dist_from_center = np.sqrt((X - effective_rad) ** 2 + (Y - effective_rad) ** 2)
    patch_mask = np.zeros((2 * effective_rad + 1, 2 * effective_rad + 1))

    val = np.logspace(0, 7, ring + 1, base=2)
    val = (val * 2) - 1
    r = np.arange(rad, effective_rad + 1, border)
    r = r[::-1]

    for i in range(len(r)):
        patch_mask[dist_from_center < r[i]] = int(val[i])

    return patch_mask

def make_preprocessing(config_dico, output_filename):
    calibFile = config_dico['camera_calibration_file']
    rad = config_dico['rad']
    diam = 2*rad + 1
    ring = config_dico['ring']
    border = config_dico['border']
    sig = [config_dico['sigma']]
    cut_off = [config_dico['cut_off']]
    testReBlur = config_dico['testReBlur']
    offset, lens, alpha, Lens_base_Yx, Lens_base_Yy = xml_reader(calibFile)

    # Read input image
    raw_image = Image.open(config_dico['filename_rgb_in'])
    image_rgb = raw_image.convert('RGB')



    #Verification img
    test_img = image_rgb.copy()
    pixel = test_img.load()
    # Parameters

    w_im = raw_image.width
    h_im = raw_image.height



    C0_im = [int(w_im/2), int(h_im/2)] # 3840/2 = 1920, 2160/2 = 1080
    C0_ll = [C0_im[0] + int(offset[0]), C0_im[1] - int(offset[1])]     #
    cX_ll, cY_ll = C0_ll

    Lens_base_Yx_pix = abs(Lens_base_Yx) * lens
    Lens_base_Yy_pix = abs(Lens_base_Yy) * lens

    deltaX = Lens_base_Yx_pix

    #print(f'compute center : ({C0_im[0] + int(offset[0]), C0_im[1] - int(offset[1])})')

    if (alpha > math.pi / 4):
        image_rgb = image_rgb.transpose(Image.TRANSPOSE)
        C0_ll = [cY_ll, cX_ll]
        cX_ll, cY_ll = C0_ll

        deltaX = Lens_base_Yy_pix

    print(f'center LL : ({cX_ll, cY_ll})')

     # Verification img
    test_img = image_rgb.copy()
    pixel = test_img.load()
    #test_img.show()

    #Used to check on test img if the center is computed correctly
    colorPatch(cX_ll, cY_ll, 5, (126,255,126),pixel)

    upNum = (cY_ll - lens*0.5)/(lens*0.5*np.sqrt(3))
    downNum = (h_im - (cY_ll+lens*0.5))/(lens*0.5*np.sqrt(3))
    Num_LL_y = int(upNum+1+downNum)

    leftNum = (cX_ll - lens*0.5)/lens
    rightNum = (w_im -(cX_ll-lens*0.5))/lens
    if(leftNum - int(leftNum) > 0.5) or (rightNum - int(rightNum) >= 0.5):
        Num_LL_x = int(leftNum)+1+int(rightNum)
    else:
        Num_LL_x = int(leftNum) + int(rightNum)


    if (alpha > math.pi / 4):
        firstX = cX_ll - (int(leftNum) * lens) - lens * 0.5
    else :
        firstX = cX_ll - (int(leftNum) * lens)

    #firstY = cY_ll - (int(upNum) * Lens_base_Yy_pix)
    firstY = cY_ll - (int(upNum) * lens*0.5*np.sqrt(3))
    #print(f'num LL : ({Num_LL_x, Num_LL_y})')
    #print(f'first LL : ({firstX, firstY})')

    #Used to check on test img if the first micro-image is found correctly
    colorPatch(int(firstX), int(firstY), 5, (126, 126, 255), pixel)

    mask = np.zeros((h_im, w_im), dtype=np.uint8)
    circlePatch = distFromCenterXringYborderLogScale(rad,ring, border)
    r = circlePatch.shape[0] // 2

    fY = firstY
    for a_ll_y in range(0, Num_LL_y - 1):
        if a_ll_y % 2 == 0:
            LL_cx = firstX
        else:
            #LL_cx = firstX - Lens_base_Yx_pix
            LL_cx = firstX + deltaX
        for a_ll_x in range(0, Num_LL_x - 1):
            pixel[LL_cx, fY] = (255,0,0)
            # for circle
            try:
                mask[int(fY - r):int(fY + r) + 1, int(LL_cx - r): int(LL_cx + r) + 1] = np.clip(mask[int(fY - r):int(fY + r) + 1, int(LL_cx - r): int(LL_cx + r) + 1] + circlePatch.astype(float), 0,255).astype(np.uint8)
            except:
                print(f"Error in generating mask for pos ({LL_cx},{fY})")
            LL_cx = LL_cx + (lens)
        #test_img.show()
        fY = fY + lens*0.5*np.sqrt(3)

    # test_img.show()



    img_array = np.asarray(image_rgb)

    for c in cut_off:
        mask_c = mask < c
        mask_name = f"{config_dico['pre_processed_output_path']}mask_circleRad{rad}Ring{ring}Bord{border}CutOff{c}.png"
        imsave(mask_name,mask_c)

    out_partial_blurr = img_array.copy()
    temp = img_array.copy()


    if testReBlur == 'true' :
        for i in range(len(sig)):
            temp[:, :, 0] = gaussian_filter(temp[:, :, 0], sig[i])
            temp[:, :, 1] = gaussian_filter(temp[:, :, 1], sig[i])
            temp[:, :, 2] = gaussian_filter(temp[:, :, 2], sig[i])

            out_partial_blurr[mask < cut_off[i]] = temp[mask < cut_off[i]]
    else :
        for i in range(len(sig)):
            temp[:, :, 0] = gaussian_filter(img_array[:, :, 0], sig[i])
            temp[:, :, 1] = gaussian_filter(img_array[:, :, 1], sig[i])
            temp[:, :, 2] = gaussian_filter(img_array[:, :, 2], sig[i])

            out_partial_blurr[mask < cut_off[i]] = temp[mask < cut_off[i]]


    final = np.transpose(out_partial_blurr, (1, 0, 2))
    # final = np.transpose(GD, (1,0,2))
    img = Image.fromarray(final, 'RGB')
    # img.save(f'blurredRad{rad}Sig{sig}.png')
    img.save(output_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', help='Path to the config file')
    parser.add_argument('-o', help='Output path name')
    parser.add_argument('-i', help='Input file name')
    args = parser.parse_args()

    input_file = args.i
    config_file = args.cfg
    output_path_name = args.o
    
    if config_file is None:
        config_dico = {}
        config_dico['filename_rgb_in'] = "origami01.png"

        # config_dico['filename_rgb_in'] = "img01.png"
        # config_dico['filename_rgb_in'] = "origami.png"
        
        config_dico['output_path'] = "./"
        config_dico['pre_processed_output_path'] = config_dico['output_path'] # besoin d'écrire ça pour que ça marche avec le pipeline

        config_dico['camera_calibration_file'] = "CalibData_DenseLightField_Nagoya.xml"
        # config_dico['camera_calibration_file'] = "dataset/Ornito/R5_calib.xml"
        # config_dico['camera_calibration_file'] = "CalibData_Modif.xml"

        config_dico['testReBlur'] = False
        config_dico['rad'] = 11
        config_dico['ring'] = 3
        config_dico['border'] = 1
        config_dico['sigma'] = 2.0
        config_dico['cut_off'] = 250

        if config_dico['testReBlur'] == True :
            output_name = f"{config_dico['output_path']}{config_dico['filename_rgb_in'].split('.')[0]}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}_TestReBlur.png"
        else :
            output_name = f"{config_dico['output_path']}{config_dico['filename_rgb_in'].split('.')[0]}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}.png"
    
    else :
        config_dico = get_config_dict(config_file)
        config_dico['pre_processed_output_path'] = config_dico['output_path'] + "pre_processing_line/"
        output_name = output_path_name

    make_preprocessing(config_dico, output_name)
