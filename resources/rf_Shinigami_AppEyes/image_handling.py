from __future__ import print_function
from builtins import range
from builtins import object
import io
import os
from PIL import Image
import random, string

class image_handling(object):
    """
    This library is used for image handling
    """
    def __init__(self):
        Image.MAX_IMAGE_PIXELS = None
    
    def combine_images_horiz(self,img_left,img_right,path,keep_original=False):
        """
        Combines images horizontally
        
        *Arguments:*
        - _img_left_ - Image path for the left image
        - _img_right_ - Image path for the right image
        - _path_ - Path of resulting image
        - _keep_original_ - (Optional) (Boolean) True if original images should be kept. False to delete. False by default.
        """
        
        # Open images to combine
        left_image = Image.open(img_left)
        right_image = Image.open(img_right)
        
        # Determine dimensions of new, combined image
        new_width = left_image.size[0]+right_image.size[0]
        new_height = max(left_image.size[1],right_image.size[1])
        
        ### Create new image ###
        target_img = Image.new("RGB",(new_width,new_height),color=(255,255,255))    # Create template image
        target_img.paste(left_image, (0,0))                                         # Paste left image on left
        target_img.paste(right_image, (left_image.size[0],0))                       # Paste right image with offset
        target_img.save(path,quality=100,optimize=True)                             # Save resulting image
        
        if not keep_original:
            # Delete original images
            if path != img_left:
                os.remove(img_left)
            if path != img_right:
                os.remove(img_right)
        
    def combine_images_vert(self,img_top,img_bottom,path,keep_original=False):
        """
        Combines images vertically
        
        *Arguments:*
        - _img_top_ - Image path for the top image
        - _img_bottom_ - Image path for the bottom image
        - _path_ - Path of resulting image
        - _keep_original_ - (Optional) (Boolean) True if original images should be kept. False to delete. False by default.
        """
        # Open images to combine
        top_image = Image.open(img_top)
        bottom_image = Image.open(img_bottom)
        
        # Determine dimensions of new, combined image
        new_width = max(top_image.size[0],bottom_image.size[0])
        new_height = top_image.size[1]+bottom_image.size[1]
        
        ### Create new image ###
        target_img = Image.new("RGB",(new_width,new_height),color=(255,255,255))    # Create template image
        target_img.paste(top_image, (0,0))                                          # Paste top image on top
        target_img.paste(bottom_image, (0,top_image.size[1]))                       # Paste bottom image with offset
        target_img.save(path,quality=100,optimize=True)                             # Save resulting image
        
        if not keep_original:
            # Delete original images
            if path != img_top:
                os.remove(img_top) 
            if path != img_bottom:
                os.remove(img_bottom)

    def combine_and_save_images_in_map(self,img_map, path, keep_original=False):
        """
        Combines images in a map of image files and saves the file
        
        *Arguments:*
        - _img_map_ - A map (2-D list) of image paths
        - _path_ - Path name of file to save
        - _keep_original_ - (Optional) (Boolean) True if original images should be kept. False to delete. False by default.
        """
        # Generate random string for session's image
        rand_string = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
        # Go through img rows in img_map and combine rows vertically
        for row_num, row in enumerate(img_map):
            row_image_name = path + '.img_row_' + rand_string + '.png'
            # Go through each img in row and combine images horizontally
            for img_num, img in enumerate(row):
                # If first image in row, save as base
                if img_num == 0:
                    if keep_original:
                        # Make a copy if original is to be kept
                        left_image = Image.open(img)
                        left_image.save(row_image_name,quality=100,optimize=True)
                    else:
                        # Rename image
                        os.rename(img, row_image_name)
                    continue
                else:
                    self.combine_images_horiz(row_image_name,img,row_image_name,keep_original)
            # If first image in column, save as base
            if row_num == 0:
                if keep_original:
                    Image.open(row_image_name).save(path,quality=100,optimize=True)
                else:
                    os.rename(row_image_name,path)
            else:
                self.combine_images_vert(path,row_image_name,path,keep_original)

    def convert_to_jpg(self,input_path,output_path,quality_value=100,keep_original=False):
        """
        Converts the image to a JPEG
        
        *Arguments:*
        - _input_path_ - Path of image to convert
        - _output_path_ - Path of converted image to output
        - _quality_value_ - (Optional) Percent of image quality to maintain. Set to 100 by default.
        - _keep_original_ - (Optional) (Boolean) True if original image should be kept. False to delete. False by default.
        """    
        input_img = Image.open(input_path)
        input_img = input_img.convert('RGB')
        input_img.save(input_path,quality=quality_value,optimize=True)
        
        # Create output image
        output_img = Image.new(input_img.mode,input_img.size,color=(255,255,255))
        output_img.paste(input_img, (0,0))
        output_img.convert('RGB')
        output_img.save(output_path,quality=quality_value,optimize=True)
        
        if not keep_original and output_path != input_path:
            os.remove(input_path)
        
    def resize_image(self,input_path,output_path,width=None,height=None,maintain_ratio=True,keep_original=False):
        """
        Resizes the given image to the given dimensions
            *Arguments:*
        - _input_path_ - Path of image to resize
        - _output_path_ - Path of resized image to output
        - _width_ - (Optional) New width to resize image to. Set to None by default
        - _height_ - (Optional) New height to resize image to. Ignored if width is provided and maintain_ratio is set to True. Set to None by default
        - _maintain_ratio_ - (Optional) (Boolean) True if image aspect ratio is to be maintained. False to override ratio. Set to True by default
        - _keep_original_ - (Optional) (Boolean) True if original image should be kept. False to delete.  False by default.
        """
        image = Image.open(input_path)
        
        if maintain_ratio:
            # Width is provided
            if width:
                new_width = width
                # Calculate new height
                height_width_ratio = float(image.size[1])/float(image.size[0])
                new_height = int(round(width * height_width_ratio))
            # Only height is provided
            elif height:
                # Calculate new width
                width_height_ratio = float(image.size[0])/float(image.size[1])
                new_width = int(round(height * width_height_ratio))
                new_height = height
            # Neither dimensions were provided
            else:
                raise ValueError("No dimensions were given to resize image!")
        else:
            # Check if dimensions provided are valid
            if (not width or not height):
                raise ValueError("Invalid dimensions were given to resize image!")
            else:
                new_width = width
                new_height = height
        
        image = image.resize((new_width,new_height),Image.ANTIALIAS)
        image.save(output_path,quality=100,optimize=True)
        
        if not keep_original and output_path != input_path:
            os.remove(input_path)
        
    def get_image_size(self,path):
        """
        Returns the dimensions of the image
        
        *Arguments:*
        - _path_ - Path name of file
        
        *Returns:*
        - _width_ - Width of image
        - _height_ - Height of image
        """
        img_file = Image.open(path)
        print(img_file.size)
        return img_file.size
        
    def crop_image(self,path,left,top,width,height):
        """
        Crops image to given dimensions
        
        *Arguments:*
        - _path_ - Image to crop
        - _left_ - Left coordinate to start cropped image
        - _top_ - Top coordinate to start cropped image
        - _width_ - Width of resulting image
        - _height_ - Height of resulting image
        """
        cropped_img = Image.new("RGB",(width,height),color=(255,255,255))
        orig_img = Image.open(path)
        cropped_img.paste(orig_img,(-left,-top))
        cropped_img.save(path,quality=100,optimize=True)