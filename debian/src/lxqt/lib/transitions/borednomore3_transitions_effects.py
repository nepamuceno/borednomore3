"""
Effects Transitions: Pixelate, Blur, Flip, Door, Barn, Peel, Wave, Glitch, Noise, Drift, etc.
"""
import cv2
import numpy as np
import random


class EffectTransitions:
    def __init__(self, screen_width, screen_height, debug, tmp_dir):
        self.w = screen_width
        self.h = screen_height
        self.debug = debug
        self.tmp_dir = tmp_dir
    
    def generate(self, family, old_img, new_img, direction, num_frames):
        generators = {
            "pixelate": self.pixelate,
            "blur": self.blur,
            "flip": self.flip,
            "door": self.door,
            "barn": self.barn,
            "peel": self.peel,
            "wave": self.wave,
            "glitch": self.glitch,
            "noise": self.noise,
            "drift": self.drift,
            "blinds": self.blinds,
            "random-blocks": self.random_blocks,
        }
        
        if family in generators:
            return generators[family](old_img, new_img, direction, num_frames)
        
        # Fallback to simple crossfade
        return self.fade(old_img, new_img, num_frames)
    
    def fade(self, old_img, new_img, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = cv2.addWeighted(old_img, 1.0 - progress, new_img, progress, 0)
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def pixelate(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            pixel_factor = int(1 + (1.0 - abs(progress - 0.5) * 2) * 30)
            base = old_img if progress < 0.5 else new_img
            temp = cv2.resize(base, (self.w // pixel_factor, self.h // pixel_factor))
            pixelated = cv2.resize(temp, (self.w, self.h), interpolation=cv2.INTER_NEAREST)
            frame = cv2.addWeighted(old_img, 1.0 - progress, new_img, progress, 0)
            frame = cv2.addWeighted(frame, 0.5, pixelated, 0.5, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def blur(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            blur_amount = int(1 + (1.0 - abs(progress - 0.5) * 2) * 30)
            if blur_amount % 2 == 0:
                blur_amount += 1
            base = old_img if progress < 0.5 else new_img
            blurred = cv2.GaussianBlur(base, (blur_amount, blur_amount), 0)
            frame = cv2.addWeighted(old_img, 1.0 - progress, new_img, progress, 0)
            frame = cv2.addWeighted(frame, 0.5, blurred, 0.5, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def flip(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "horizontal":
                scale_x = abs(np.cos(progress * np.pi))
                base = old_img if progress < 0.5 else cv2.flip(new_img, 1)
                M = np.float32([[scale_x, 0, self.w * (1 - scale_x) / 2], [0, 1, 0]])
            else:  # vertical
                scale_y = abs(np.cos(progress * np.pi))
                base = old_img if progress < 0.5 else cv2.flip(new_img, 0)
                M = np.float32([[1, 0, 0], [0, scale_y, self.h * (1 - scale_y) / 2]])
            
            frame = cv2.warpAffine(base, M, (self.w, self.h))
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def door(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            swing_width = int(self.w * (1.0 - progress))
            
            if swing_width > 0:
                scale = 1.0 - progress * 0.5
                new_h = max(1, int(self.h * scale))
                y_offset = (self.h - new_h) // 2
                
                if direction == "left":
                    door_part = old_img[:, :swing_width]
                    resized = cv2.resize(door_part, (swing_width, new_h))
                    frame[y_offset:y_offset+new_h, :swing_width] = resized
                else:  # right
                    door_part = old_img[:, -swing_width:]
                    resized = cv2.resize(door_part, (swing_width, new_h))
                    frame[y_offset:y_offset+new_h, -swing_width:] = resized
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def barn(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            if direction == "horizontal":
                door_width = int((self.w // 2) * (1.0 - progress))
                if door_width > 0:
                    frame[:, :door_width] = old_img[:, :door_width]
                    frame[:, -door_width:] = old_img[:, -door_width:]
            else:  # vertical
                door_height = int((self.h // 2) * (1.0 - progress))
                if door_height > 0:
                    frame[:door_height, :] = old_img[:door_height, :]
                    frame[-door_height:, :] = old_img[-door_height:, :]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def peel(self, old_img, new_img, corner, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            peel_w, peel_h = int(self.w * (1.0 - progress)), int(self.h * (1.0 - progress))
            
            if corner == "top-left" and peel_w > 0 and peel_h > 0:
                frame[:peel_h, :peel_w] = old_img[:peel_h, :peel_w]
            elif corner == "top-right" and peel_w > 0 and peel_h > 0:
                frame[:peel_h, -peel_w:] = old_img[:peel_h, -peel_w:]
            elif corner == "bottom-left" and peel_w > 0 and peel_h > 0:
                frame[-peel_h:, :peel_w] = old_img[-peel_h:, :peel_w]
            elif corner == "bottom-right" and peel_w > 0 and peel_h > 0:
                frame[-peel_h:, -peel_w:] = old_img[-peel_h:, -peel_w:]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def wave(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            if direction == "horizontal":
                for y in range(self.h):
                    wave_offset = int(20 * np.sin((y / self.h * 10 + progress * 5) * np.pi))
                    cut_x = min(self.w - 1, max(0, int(progress * self.w) + wave_offset))
                    if cut_x < self.w:
                        frame[y, :cut_x] = new_img[y, :cut_x]
            else:  # vertical
                for x in range(self.w):
                    wave_offset = int(20 * np.sin((x / self.w * 10 + progress * 5) * np.pi))
                    cut_y = min(self.h - 1, max(0, int(progress * self.h) + wave_offset))
                    if cut_y < self.h:
                        frame[cut_y:, x] = new_img[cut_y:, x]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def glitch(self, old_img, new_img, glitch_type, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if glitch_type == "normal" or glitch_type not in ["rgb-split"]:
                frame = old_img.copy()
                glitch_amount = int(progress * 50)
                for _ in range(glitch_amount):
                    y = random.randint(0, self.h - 20)
                    h_slice = random.randint(5, 20)
                    offset = random.randint(-30, 30)
                    slice_img = new_img[y:y+h_slice, :] if random.random() > 0.5 else old_img[y:y+h_slice, :]
                    M = np.float32([[1, 0, offset], [0, 1, 0]])
                    slice_img = cv2.warpAffine(slice_img, M, (slice_img.shape[1], slice_img.shape[0]))
                    frame[y:y+h_slice, :] = slice_img
                frame = cv2.addWeighted(frame, 1.0 - progress, new_img, progress, 0)
            else:  # rgb-split
                frame = old_img.copy()
                offset = int((1.0 - abs(progress - 0.5) * 2) * 20)
                b, g, r = cv2.split(frame)
                M_r = np.float32([[1, 0, offset], [0, 1, 0]])
                M_b = np.float32([[1, 0, -offset], [0, 1, 0]])
                r = cv2.warpAffine(r, M_r, (self.w, self.h))
                b = cv2.warpAffine(b, M_b, (self.w, self.h))
                frame = cv2.merge([b, g, r])
                frame = cv2.addWeighted(frame, 1.0 - progress, new_img, progress, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def noise(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            noise = np.random.randint(0, 256, old_img.shape, dtype=np.uint8)
            noise_amount = 1.0 - abs(progress - 0.5) * 2
            base = old_img if progress < 0.5 else new_img
            frame = cv2.addWeighted(base, 1.0 - noise_amount, noise, noise_amount, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def drift(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            drift = int(progress * 50)
            
            if direction == "left":
                M = np.float32([[1, 0, -drift], [0, 1, 0]])
            elif direction == "right":
                M = np.float32([[1, 0, drift], [0, 1, 0]])
            elif direction == "up":
                M = np.float32([[1, 0, 0], [0, 1, -drift]])
            else:  # down
                M = np.float32([[1, 0, 0], [0, 1, drift]])
            
            old_transformed = cv2.warpAffine(old_img, M, (self.w, self.h))
            frame = cv2.addWeighted(old_transformed, 1.0 - progress, new_img, progress, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def blinds(self, old_img, new_img, direction, num_frames):
        frames = []
        num_slats = 20
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            if direction == "horizontal":
                slat_height = self.h // num_slats
                for slat in range(num_slats):
                    y_start = slat * slat_height
                    y_end = min((slat + 1) * slat_height, self.h)
                    reveal_height = int(progress * (y_end - y_start))
                    if reveal_height > 0:
                        frame[y_start:y_start+reveal_height, :] = new_img[y_start:y_start+reveal_height, :]
            else:  # vertical
                slat_width = self.w // num_slats
                for slat in range(num_slats):
                    x_start = slat * slat_width
                    x_end = min((slat + 1) * slat_width, self.w)
                    reveal_width = int(progress * (x_end - x_start))
                    if reveal_width > 0:
                        frame[:, x_start:x_start+reveal_width] = new_img[:, x_start:x_start+reveal_width]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def random_blocks(self, old_img, new_img, direction, num_frames):
        frames = []
        block_size = 50
        blocks = [(x, y) for y in range(0, self.h, block_size) for x in range(0, self.w, block_size)]
        random.shuffle(blocks)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            num_blocks_to_reveal = int(progress * len(blocks))
            
            for idx in range(num_blocks_to_reveal):
                x, y = blocks[idx]
                x2, y2 = min(x + block_size, self.w), min(y + block_size, self.h)
                frame[y:y2, x:x2] = new_img[y:y2, x:x2]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
