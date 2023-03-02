import argparse
import os
import sys

import cv2
import numpy as np
# from PIL import Image, ImageOps

sys.path.append(os.path.dirname(os.path.dirname(__file__)) + "\\Real_ESRGAN")

from basicsr.archs.rrdbnet_arch import RRDBNet

from realesrgan.archs.srvgg_arch import SRVGGNetCompact
from realesrgan.utils import RealESRGANer


def enhancement(filepath, dirpath, ext, scale=4):
    print("enhancement",filepath, dirpath, ext,scale)
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default=filepath, help='输入图像')
    parser.add_argument(
        '-n',
        '--model_name',
        type=str,
        default='RealESRGAN_x4plus',
        help=('Model names: RealESRGAN_x4plus | RealESRNet_x4plus | RealESRGAN_x4plus_anime_6B | RealESRGAN_x2plus'
              'RealESRGANv2-anime-xsx2 | RealESRGANv2-animevideo-xsx2-nousm | RealESRGANv2-animevideo-xsx2'
              'RealESRGANv2-anime-xsx4 | RealESRGANv2-animevideo-xsx4-nousm | RealESRGANv2-animevideo-xsx4'))
    parser.add_argument('-o', '--output', type=str, default=dirpath, help='输出文件夹')
    parser.add_argument('-s', '--outscale', type=float, default=4, help='图像的最终升采样比例')
    parser.add_argument('--suffix', type=str, default='enhanced', help='增强的图像的文件后缀')
    parser.add_argument('-t', '--tile', type=int, default=0, help='Tile大小，0表示测试期间没有Tile')
    parser.add_argument('--tile_pad', type=int, default=10, help='Tile的padding属性')
    parser.add_argument('--pre_pad', type=int, default=0, help='每个边框的padding尺寸')
    parser.add_argument('--face_enhance', action='store_true', help='使用GFPGAN来增强面部')
    parser.add_argument('--half', action='store_true', help='在生成过程中使用半精度')
    parser.add_argument(
        '--alpha_upsampler',
        type=str,
        default='realesrgan',
        help='alpha通道的上采样器。选项：realesrgan | bicubic')
    parser.add_argument(
        '--ext',
        type=str,
        default=ext,
        help='图像扩展名。选项：auto|jpg|png，自动意味着使用与输入相同的扩展名。')
    # args = parser.parse_args()
    args = parser.parse_args(args=[])

    # 根据模型名称确定模型
    args.model_name = args.model_name.split('.')[0]
    if args.model_name in ['RealESRGAN_x4plus', 'RealESRNet_x4plus']:  # x4 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
    elif args.model_name in ['RealESRGAN_x4plus_anime_6B']:  # x4 RRDBNet model with 6 blocks
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        netscale = 4
    elif args.model_name in ['RealESRGAN_x2plus']:  # x2 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        netscale = 2
    elif args.model_name in [
        'RealESRGANv2-anime-xsx2', 'RealESRGANv2-animevideo-xsx2-nousm', 'RealESRGANv2-animevideo-xsx2'
    ]:  # x2 VGG-style model (XS size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
        netscale = 2
    elif args.model_name in [
        'RealESRGANv2-anime-xsx4', 'RealESRGANv2-animevideo-xsx4-nousm', 'RealESRGANv2-animevideo-xsx4'
    ]:  # x4 VGG-style model (XS size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
        netscale = 4

    # 确定模型路径
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)) + '/Real_ESRGAN/experiments/pretrained_models/',
        args.model_name + '.pth')
    # restorer
    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        model=model,
        tile=args.tile,
        tile_pad=args.tile_pad,
        pre_pad=args.pre_pad,
        half=args.half)
    if args.face_enhance:  # 使用GFPGAN进行面部强化
        from gfpgan import GFPGANer
        face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v0.2.0/GFPGANCleanv1-NoCE-C2.pth',
            # upscale=args.outscale,
            upscale = scale,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=upsampler)
    os.makedirs(args.output, exist_ok=True)
    if os.path.isfile(args.input):
        path = args.input
        imgname, extension = os.path.splitext(os.path.basename(path))
        print("imgname",imgname)
        print("extension",extension)
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)
    #img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if len(img.shape) == 3 and img.shape[2] == 4:
        img_mode = 'RGBA'
    else:
        img_mode = None

    try:
        if args.face_enhance:
            _, _, output = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
        else:
            output, _ = upsampler.enhance(img, outscale=scale)
    except RuntimeError as error:
        print('错误', error)
        print('如果你遇到CUDA内存不足的情况，试着把--tile设置成一个较小的数字。')
        return "内存不足！"
    else:
        if args.ext == 'auto':
            extension = extension[1:]
            print("test: ", extension)
        else:
            extension = args.ext
            print("test2: ", extension)
        if img_mode == 'RGBA':  # RGBA images should be saved in png format
            extension = '.png'
        save_path = os.path.join(args.output, f'{imgname}_{args.suffix}{extension}')
        print(save_path)
        #cv2.imwrite(save_path, output)
        cv2.imencode(extension, output)[1].tofile(save_path)
        # 中文路径
        print("图片已增强")
        return save_path


if __name__ == '__main__':
    enhancement()
