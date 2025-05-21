/**
 * result.js - 处理结果页面的逻辑
 * 
 * 功能：
 * 1. 从localStorage读取保存的图片数据和位置信息
 * 2. 显示图片和位置信息
 * 3. 生成二维码
 * 4. 实现倒计时功能
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 从localStorage读取数据
    const imageDataUrl = localStorage.getItem('savedImageData');
    const locationName = localStorage.getItem('locationName');
    const locationCountry = localStorage.getItem('locationCountry');
    const coordinates = localStorage.getItem('coordinates');
    
    // 检查数据是否存在
    if (!imageDataUrl) {
        alert('没有找到图片数据，将返回首页');
        window.location.href = '../index.html';
        return;
    }
    
    // 显示图片
    const matchedImage = document.getElementById('matched-image');
    matchedImage.src = imageDataUrl;
    
    // 设置背景为原始图片
    const imageId = localStorage.getItem('imageId') || '4';
    document.body.style.backgroundImage = `url('/img/full/${imageId}.jpg')`;
    
    // 显示坐标信息
    document.getElementById('image-coords').textContent = coordinates || "8°41'S 115°16'E";
    
    // 生成二维码
    generateQRCode(imageDataUrl);
    
    // 启动倒计时
    startCountdown();
    
    // 记录事件（如果GA可用）
    if (typeof ga === 'function') {
        ga('send', 'event', 'Draw', 'view_saved_image');
    }
});

/**
 * 生成二维码
 * @param {string} imageDataUrl - 图片的Data URL
 */
function generateQRCode(imageDataUrl) {
    // 获取必要的信息
    const fullImageUrl = localStorage.getItem('fullImageUrl');
    const coordinates = localStorage.getItem('coordinates') || "8°41'S 115°16'E";
    const imageId = localStorage.getItem('imageId') || '4';
    
    // 确定图片URL
    let imageUrl;
    if (fullImageUrl) {
        imageUrl = fullImageUrl;
        console.log('使用完整图片URL: ' + fullImageUrl);
    } else {
        // 如果没有完整URL，则使用图片ID构建URL
        const baseUrl = window.location.protocol + '//' + window.location.host;
        imageUrl = baseUrl + '/img/full/' + imageId + '.jpg';
        console.log('未找到完整URL，使用构建的URL: ' + imageUrl);
    }
    
    // 构建logo URL
    const logoUrl = window.location.protocol + '//' + window.location.host + '/img/home/blue_up_logo.png';
    
    // 构建指向qr-result.html的URL，并附带所有参数
    const baseUrl = window.location.protocol + '//' + window.location.host;
    const qrUrl = baseUrl + '/draw/qr-result.html' + 
                 '?img=' + encodeURIComponent(imageUrl) + 
                 '&logo=' + encodeURIComponent(logoUrl) + 
                 '&coords=' + encodeURIComponent(coordinates);
    
    console.log('二维码URL:', qrUrl);
    
    // 生成二维码
    try {
        new QRCode(document.getElementById("qrcode"), {
            text: qrUrl,
            width: 100,
            height: 100,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.M // 中等纠错级别，平衡数据容量和纠错能力
        });
        console.log('二维码生成成功');
    } catch (error) {
        console.error('生成二维码时出错:', error);
        document.querySelector('.qrcode-text').textContent = '二维码生成失败，请重试';
    }
}

/**
 * 压缩图片
 * @param {string} imgData - 图片的Data URL
 * @param {number} quality - 压缩质量（0-1）
 * @returns {Promise<string>} 压缩后的图片Data URL
 */
function compressImage(imgData, quality) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = function() {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // 计算新尺寸，保持宽高比
                let width = img.width;
                let height = img.height;
                
                // 如果图片太大，进行缩小
                const maxDimension = 100; // 降低最大尺寸以减小数据量
                if (width > maxDimension || height > maxDimension) {
                    if (width > height) {
                        height = Math.round(height * (maxDimension / width));
                        width = maxDimension;
                    } else {
                        width = Math.round(width * (maxDimension / height));
                        height = maxDimension;
                    }
                }
                
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);
                resolve(canvas.toDataURL('image/jpeg', quality || 0.1));
            } catch (error) {
                reject(error);
            }
        };
        img.onerror = function() {
            reject(new Error('图片加载失败'));
        };
        img.src = imgData;
    });
}

/**
 * 启动倒计时
 */
function startCountdown() {
    let seconds = 30;
    const countdownElement = document.getElementById('countdown');
    
    const interval = setInterval(() => {
        seconds--;
        countdownElement.textContent = seconds + 'S';
        
        if (seconds <= 0) {
            clearInterval(interval);
            window.location.href = '../index.html'; // 倒计时结束后返回首页
        }
    }, 1000);
    
    // 点击返回按钮时清除倒计时
    document.querySelector('.back-button').addEventListener('click', function() {
        clearInterval(interval);
    });
}
