#include <stdio.h>
#include <string.h>
#include "weights.h"

#define INPUT_SIZE 784
#define OUTPUT_SIZE 10


void top(float input[INPUT_SIZE], float output[OUTPUT_SIZE]) {

    output[0] = conv1_weight[0];
    output[1] = conv1_weight[1];

}


int main() {
    float input[INPUT_SIZE];
    float output[OUTPUT_SIZE];


    memset(input, 0, sizeof(input));


    printf("正在执行\n");
    top(input, output);


    printf("完成\n");
    printf("验证: output[0] = %f, output[1] = %f\n", output[0], output[1]);

    if (output[0] == conv1_weight[0] && output[1] == conv1_weight[1]) {
        printf("权重正确\n");
    } else {
        printf("失败\n");
    }

    return 0;
}