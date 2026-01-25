"""
Basic Transitions: Slide, Rotate, Zoom, Fade, Wipe
"""
import cv2
import numpy as np


class BasicTransitions:
    def __init__(self, screen_width, screen_height, debug, tmp_dir):
        self.w = screen_width
        self.h = screen_height
        self.debug = debug
        self.tmp_dir = tmp_dir
    
    def generate(self, family, old_img, new_img, direction, num_frames, angle=90):
        if family == "slide":
            return self.slide(old_img, new_img, direction, num_frames)
        elif family == "rotate":
            return self.rotate(old_img, new_img, angle, direction, num_frames)
        elif family == "zoom":
            return self.zoom(old_img, new_img, direction, num_frames)
        elif family == "fade":
            return self.fade(old_img, new_img, direction, num_frames)
        elif family == "wipe":
            return self.wipe(old_img, new_img, direction, num_frames)
        return self.fade(old_img, new_img, "cross", num_frames)
    
    def slide(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "left":
                old_dx, new_dx, old_dy, new_dy = -int(progress * self.w), self.w - int(progress * self.w), 0, 0
            elif direction == "right":
                old_dx, new_dx, old_dy, new_dy = int(progress * self.w), -self.w + int(progress * self.w), 0, 0
            elif direction == "up":
                old_dx, new_dx, old_dy, new_dy = 0, 0, -int(progress * self.h), self.h - int(progress * self.h)
            elif direction == "down":
                old_dx, new_dx, old_dy, new_dy = 0, 0, int(progress * self.h), -self.h + int(progress * self.h)
            elif direction == "top-left":
                old_dx, new_dx = -int(progress * self.w), self.w - int(progress * self.w)
                old_dy, new_dy = -int(progress * self.h), self.h - int(progress * self.h)
            elif direction == "top-right":
                old_dx, new_dx = int(progress * self.w), -self.w + int(progress * self.w)
                old_dy, new_dy = -int(progress * self.h), self.h - int(progress * self.h)
            elif direction == "bottom-left":
                old_dx, new_dx = -int(progress * self.w), self.w - int(progress * self.w)
                old_dy, new_dy = int(progress * self.h), -self.h + int(progress * self.h)
            elif direction == "bottom-right":
                old_dx, new_dx = int(progress * self.w), -self.w + int(progress * self.w)
                old_dy, new_dy = int(progress * self.h), -self.h + int(progress * self.h)
            else:
                old_dx, new_dx, old_dy, new_dy = 0, 0, 0, 0
            
            frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
            
            old_M = np.float32([[1, 0, old_dx], [0, 1, old_dy]])
            old_transformed = cv2.warpAffine(old_img, old_M, (self.w, self.h))
            mask_old = (old_transformed.sum(axis=2) > 0).astype(np.uint8) * 255
            mask_old = cv2.merge([mask_old, mask_old, mask_old])
            frame = np.where(mask_old > 0, old_transformed, frame)
            
            new_M = np.float32([[1, 0, new_dx], [0, 1, new_dy]])
            new_transformed = cv2.warpAffine(new_img, new_M, (self.w, self.h))
            mask_new = (new_transformed.sum(axis=2) > 0).astype(np.uint8) * 255
            mask_new = cv2.merge([mask_new, mask_new, mask_new])
            frame = np.where(mask_new > 0, new_transformed, frame)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def rotate(self, old_img, new_img, angle, direction, num_frames):
        frames = []
        center = (self.w // 2, self.h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            current_angle = angle * progress if direction == "cw" else -angle * progress
            
            old_M = cv2.getRotationMatrix2D(center, current_angle, 1.0)
            old_transformed = cv2.warpAffine(old_img, old_M, (self.w, self.h))
            frame = cv2.addWeighted(old_transformed, 1.0 - progress, new_img, progress, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def zoom(self, old_img, new_img, direction, num_frames):
        frames = []
        center = (self.w // 2, self.h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "out":
                old_scale, new_scale = max(0.01, 1.0 - progress), 1.0
            elif direction == "in":
                old_scale, new_scale = 1.0, max(0.01, progress)
            else:  # pulse
                old_scale = 1.0 + 0.3 * np.sin(progress * np.pi)
                new_scale = 1.0
            
            old_M = cv2.getRotationMatrix2D(center, 0, old_scale)
            old_M[0, 2] += (self.w / 2) * (1 - old_scale)
            old_M[1, 2] += (self.h / 2) * (1 - old_scale)
            
            new_M = cv2.getRotationMatrix2D(center, 0, new_scale)
            new_M[0, 2] += (self.w / 2) * (1 - new_scale)
            new_M[1, 2] += (self.h / 2) * (1 - new_scale)
            
            old_transformed = cv2.warpAffine(old_img, old_M, (self.w, self.h))
            new_transformed = cv2.warpAffine(new_img, new_M, (self.w, self.h))
            frame = cv2.addWeighted(old_transformed, 1.0 - progress, new_transformed, progress, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def fade(self, old_img, new_img, fade_type, num_frames):
        frames = []
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if fade_type == "cross":
                frame = cv2.addWeighted(old_img, 1.0 - progress, new_img, progress, 0)
            elif fade_type == "black":
                if progress < 0.5:
                    black = np.zeros_like(old_img)
                    frame = cv2.addWeighted(old_img, 1.0 - (progress * 2), black, progress * 2, 0)
                else:
                    black = np.zeros_like(new_img)
                    frame = cv2.addWeighted(black, 1.0 - ((progress - 0.5) * 2), new_img, (progress - 0.5) * 2, 0)
            else:  # white
                if progress < 0.5:
                    white = np.full_like(old_img, 255)
                    frame = cv2.addWeighted(old_img, 1.0 - (progress * 2), white, progress * 2, 0)
                else:
                    white = np.full_like(new_img, 255)
                    frame = cv2.addWeighted(white, 1.0 - ((progress - 0.5) * 2), new_img, (progress - 0.5) * 2, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def wipe(self, old_img, new_img, direction, num_frames):
        frames = []
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            if direction == "left":
                x_cut = int((1.0 - progress) * self.w)
                frame[:, x_cut:] = new_img[:, x_cut:]
            elif direction == "right":
                x_cut = int(progress * self.w)
                frame[:, :x_cut] = new_img[:, :x_cut]
            elif direction == "up":
                y_cut = int((1.0 - progress) * self.h)
                frame[y_cut:, :] = new_img[y_cut:, :]
            elif direction == "down":
                y_cut = int(progress * self.h)
                frame[:y_cut, :] = new_img[:y_cut, :]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
