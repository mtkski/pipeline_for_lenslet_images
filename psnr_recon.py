import cv2
import numpy as np
from skimage.metrics import structural_similarity
import matplotlib.pyplot as plt
import argparse
from config_maker import get_config_dict

# path_ref = "C:/Users/Administrateur/Desktop/These/plenopticCompression/RLC1.5/Output/fujita/Res_009/"

# path = "C:/Users/Administrateur/Desktop/These/plenopticCompression/RLC1.5/Output/patchRad8/recon/"
# path = "C:/Users/Administrateur/Desktop/These/plenopticCompression/RLC1.5/Output/blurredCircleProg/"
# path = "C:/Users/Administrateur/Desktop/These/plenopticCompression/RLC1.5/Output/fujita/interpRad9/"
# path = "C:/Users/Administrateur/Desktop/These/plenopticCompression/RLC1.5/Output/origami/recon/"


#path_output = "C:/Users/Administrateur/Desktop/These/plenopticCompression/AgnosticLVC/ComprPatchPreprocessing/CircleBlur/"

start = 11
end = 11

num = 25

QP = [50]

def psnr_percent(img1, img2, prop):
    if img1.shape != img2.shape:
        raise Exception
    new_w = int(img1.shape[1]*prop)
    new_h = int(img1.shape[0]*prop)
    # print(new_w)
    rad_w = (img1.shape[1]-new_w) //2
    rad_h = (img1.shape[0]-new_h) //2
    # print(rad_w)

    new_img1 = img1[rad_h:rad_h+new_h, rad_w:rad_w+new_w]
    new_img2 = img2[rad_h:rad_h+new_h, rad_w:rad_w+new_w]
    # print(new_img1.shape)

    return cv2.PSNR(new_img1, new_img2)


def calc_psnr(config_dico, ref_images_path, images_path, output_path_name, name):
    for r in range(start, end+1):
        Table_psnr = np.zeros((len(QP)))
        Table_ssim = np.zeros((len(QP)))
        q = 0
        for qp in QP:
            mean_psnr = 0
            mean_ssim = 0

            # path_rad = path+"Rad_{:d}/QP{:d}/Res_001/".format(r, qp)
            # path_rad = path+"Rad_{:d}/origami/QP{:d}/".format(r, qp)
            # path_rad = path+"patchRad{:d}/recon/QP{:d}/fujita/".format(r, qp)
            # path_rad = path+"QP{:d}/Res_001/".format(qp)
            # path_rad = path+"Rad_{:d}/Sig0.8_0.8_0.8/recon/fujita/QP{:d}/".format(r,qp)
            # path_rad = path+"Rad_{:d}/Ring3_Bord1/Sig0.8_0.8_0.8_0.8_CutOff250_191_127_120/fujita/".format(r)
            # path_rad = path+"Rad_{:d}/Sig0.8_0.8_0.8/fujita9/".format(r)
            # path_rad = path+"Rad{:d}/s2.0-2.5_c250-49/recon/origami/QP{:d}/".format(r, qp)
            path_rad = images_path+ f"qp{qp}/"
            # path_rad = path+"Rad_{:d}/Sig0.8_2.0_2.8/fujita2/".format(r)

            
            for i in range(1, num+1):
                ref = cv2.imread(ref_images_path+"image_{:03d}.png".format(i))
                img = cv2.imread(path_rad+"image_{:03d}.png".format(i))
                #psnr
                # psnr = cv2.PSNR(ref, img)
                psnr = psnr_percent(ref, img,1) #0.98 -> 96%
                mean_psnr += psnr
                ssim = structural_similarity(ref, img, channel_axis=2)
                mean_ssim += ssim

            mean_psnr /= num
            mean_ssim /= num
            Table_psnr[q] = mean_psnr
            Table_ssim[q] = mean_ssim
            q += 1


        # print(f"rad : {r} - PSNR ",np.round(Table_psnr,2))
        # print(f"rad : {r} - SSIM ",np.round(Table_ssim,4))
        output_path_name = f"{output_path_name}psnr_{name}_qp{config_dico['qp']}.txt"
        with open(output_path_name, 'w') as file:
            file.write(f"rad : {r} - PSNR {np.round(Table_psnr,2)}\n")
            file.write(f"rad : {r} - SSIM {np.round(Table_ssim,4)}\n")

        #np.savetxt(path_output+"rad{:d}/QPtableOrig.csv".format(r), Table, delimiter=', ')


if __name__ == "__main__":
    print("___________________PSNR___________________")
    parser = argparse.ArgumentParser()
    parser.add_argument('-ref', help='Path to the config file')
    parser.add_argument('-i', help='Input file name')
    parser.add_argument('-o', help='Output path name')
    parser.add_argument('-cfg', help='Path to the config file')
    parser.add_argument('-name', help='Name of the output file')

    args = parser.parse_args()

    ref_image_name_path = args.ref
    image_name_path = args.i
    output_path_name = args.o
    config_file = args.cfg
    name = args.name
    config_dico = get_config_dict(config_file)
    print("Calculating PSNR ...")
    calc_psnr(config_dico, config_dico['RLC_ref_path'], image_name_path, output_path_name, name)

