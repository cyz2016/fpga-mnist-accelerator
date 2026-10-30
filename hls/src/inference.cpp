#include <cstdio>
#include <cmath>
#include <cstring>
#include "weights.h"

// ================= 工具函数 =================
void print_matrix(const char* name, const float* data, int n) {
    printf("=== %s (n=%d) ===\n", name, n);
    float sum = 0, mx = -1e30, mn = 1e30;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (data[i] > mx) mx = data[i];
        if (data[i] < mn) mn = data[i];
    }
    printf("  Mean: %.6f  Max: %.6f  Min: %.6f\n\n", sum / n, mx, mn);
}

// ================= 卷积层 =================
void conv2d(const float* input, const float* weight, const float* bias,
            float* output,
            int in_ch, int out_ch, int in_h, int in_w, int kh, int kw) {
    int out_h = in_h - kh + 1;
    int out_w = in_w - kw + 1;
    memset(output, 0, out_ch * out_h * out_w * sizeof(float));

    for (int oc = 0; oc < out_ch; oc++) {
        for (int ic = 0; ic < in_ch; ic++) {
            for (int oh = 0; oh < out_h; oh++) {
                for (int ow = 0; ow < out_w; ow++) {
                    float sum = 0;
                    for (int fh = 0; fh < kh; fh++) {
                        for (int fw = 0; fw < kw; fw++) {
                            int in_idx = ic * in_h * in_w + (oh + fh) * in_w + (ow + fw);
                            int w_idx  = oc * in_ch * kh * kw + ic * kh * kw + fh * kw + fw;
                            sum += input[in_idx] * weight[w_idx];
                        }
                    }
                    int out_idx = oc * out_h * out_w + oh * out_w + ow;
                    output[out_idx] += sum;
                }
            }
        }
        // 加 bias
        for (int oh = 0; oh < out_h; oh++) {
            for (int ow = 0; ow < out_w; ow++) {
                output[oc * out_h * out_w + oh * out_w + ow] += bias[oc];
            }
        }
    }
}

// ================= ReLU =================
void relu(float* data, int n) {
    for (int i = 0; i < n; i++) {
        if (data[i] < 0) data[i] = 0;
    }
}

// ================= MaxPool 2x2 =================
void maxpool2x2(const float* input, float* output,
                int ch, int in_h, int in_w) {
    int out_h = in_h / 2;
    int out_w = in_w / 2;
    for (int c = 0; c < ch; c++) {
        for (int oh = 0; oh < out_h; oh++) {
            for (int ow = 0; ow < out_w; ow++) {
                float mx = -1e30;
                for (int fh = 0; fh < 2; fh++) {
                    for (int fw = 0; fw < 2; fw++) {
                        int idx = c * in_h * in_w + (oh * 2 + fh) * in_w + (ow * 2 + fw);
                        if (input[idx] > mx) mx = input[idx];
                    }
                }
                output[c * out_h * out_w + oh * out_w + ow] = mx;
            }
        }
    }
}

// ================= 全连接层 =================
void fc(const float* input, const float* weight, const float* bias,
        float* output, int in_size, int out_size) {
    for (int o = 0; o < out_size; o++) {
        float sum = 0;
        for (int i = 0; i < in_size; i++) {
            sum += input[i] * weight[o * in_size + i];
        }
        output[o] = sum + bias[o];
    }
}

// ================= 主推理 =================
int main() {
    // 输入: 28x28 全 0.5 归一化
    const int INPUT_SIZE = 28 * 28;
    float input[INPUT_SIZE];
    float norm_input = (0.5f - 0.1307f) / 0.3081f;
    for (int i = 0; i < INPUT_SIZE; i++) {
        input[i] = norm_input;
    }
    printf("NORM_INPUT = %.8f\n\n", norm_input);

    // --- Conv1: 1x28x28 -> 6x24x24 ---
    float conv1_out[6 * 24 * 24];
    conv2d(input, w_conv1_weight, w_conv1_bias, conv1_out,
           1, 6, 28, 28, 5, 5);
    relu(conv1_out, 6 * 24 * 24);
    print_matrix("Conv1 (after ReLU)", conv1_out, 6 * 24 * 24);

    // --- Pool1: 6x24x24 -> 6x12x12 ---
    float pool1_out[6 * 12 * 12];
    maxpool2x2(conv1_out, pool1_out, 6, 24, 24);
    print_matrix("Pool1", pool1_out, 6 * 12 * 12);

    // --- Conv2: 6x12x12 -> 16x8x8 ---
    float conv2_out[16 * 8 * 8];
    conv2d(pool1_out, w_conv2_weight, w_conv2_bias, conv2_out,
           6, 16, 12, 12, 5, 5);
    relu(conv2_out, 16 * 8 * 8);
    print_matrix("Conv2 (after ReLU)", conv2_out, 16 * 8 * 8);

    // --- Pool2: 16x8x8 -> 16x4x4 ---
    float pool2_out[16 * 4 * 4];
    maxpool2x2(conv2_out, pool2_out, 16, 8, 8);
    print_matrix("Pool2", pool2_out, 16 * 4 * 4);

    // --- FC1: 256 -> 120 ---
    float fc1_out[120];
    fc(pool2_out, w_fc1_weight, w_fc1_bias, fc1_out, 256, 120);
    relu(fc1_out, 120);
    print_matrix("FC1 (after ReLU)", fc1_out, 120);

    // --- FC2: 120 -> 10 ---
    float fc2_out[10];
    fc(fc1_out, w_fc2_weight, w_fc2_bias, fc2_out, 120, 10);
    print_matrix("FC2 (output logits)", fc2_out, 10);

    printf("=== C++ Inference Results ===\n");
    for (int i = 0; i < 10; i++) {
        printf("Output[%d]: %.8f\n", i, fc2_out[i]);
    }

    return 0;
}