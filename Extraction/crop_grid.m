clear;
clc;

img = imread("Screenshots/ride.jpeg");

imggray = im2gray(im2double(img));
imb = imgaussfilt(imggray, 3);

isblack = imggray < 0.2;



[img, BW] = imremoveborder(img, isblack);



%%
% Find lines
[H,T,R] = hough(BW);
P  = houghpeaks(H,13+8,'threshold',ceil(0.1*max(H(:))));
lines = houghlines(BW,T,R,P,'FillGap',5,'MinLength',300);

% Get vertical and horizontal lines
points1 = cat(1,lines.point1);
delta = points1 - cat(1,lines.point2);
is_vertical = abs(delta(:, 1)) < 0.1;
is_horizontal = abs(delta(:, 2)) < 0.1;
verts = sort(points1(is_vertical, 1));
horis = sort(points1(is_horizontal, 2));

yn = length(horis)-1;
xn = length(verts)-1;

% Extract images and remove borders (i.e. lines that ended up in the icon
imcells = cell(yn, xn);
p = 1;
for yi = 1:yn
    for xi = 1:xn
        ys = horis(yi:(yi+1));
        xs = verts(xi:(xi+1));

        imgc = img(ys(1):ys(2), xs(1):xs(2), :);
        isborder = BW(ys(1):ys(2), xs(1):xs(2), :);

        [imgc] = imremoveborder(imgc, isborder);
        imcells{yi, xi} = imgc;
        
        subplot(yn, xn, p);
        imshow(imgc)
        p = p +1;
    end
end


function [img_crop, border_pixels_crop] = imremoveborder(img, border_pixels)
    % border pixels set true if they are the same color as the border
    gim = border_pixels;
    
    % Get co
    CC = bwconncomp(gim);

    [h,w] = size(gim);
    border = false([h,w]);
    for i = 1:CC.NumObjects
        idxs = CC.PixelIdxList{i};

        % if the connected component sits at the edge of the image
        % set its pixels true in the border
        [x, y] = ind2sub([h,w], idxs);
        subs = [x, y];
        min_b = min(subs);
        max_b = max(subs);
        border(idxs) = sum(min_b - 1) < 0.1 || sum(abs(max_b - [h,w]))  < 0.1;
    end

    % If there are any set pixels in the border
    if any(border)
        % invert the border and get the largest CC
        main = ~border;
        CC2 = bwconncomp(main);
        
        max_i = 1;
        if CC2.NumObjects > 1
            CC2size = cellfun(@(x) length(x), CC.PixelIdxList);
            [~, max_i] = max(CC2size);
        end
        idxs = CC2.PixelIdxList{max_i};

        % crop bounds
        [x, y] = ind2sub([h,w], idxs);
        xs = min(x);
        xe = max(x);
        ys = min(y);
        ye = max(y);
        
        img_crop = img(xs:xe, ys:ye, :);
        border_pixels_crop = border_pixels(xs:xe, ys:ye, :);
    else
        img_crop = img;
        border_pixels_crop = border_pixels;
    end
end

