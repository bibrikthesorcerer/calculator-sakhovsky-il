#include <gtest/gtest.h>

extern "C" {
#include "../../src/calculator.h"
}

// Tests for getters and setters
TEST(ModeSetter, SetInt) { EXPECT_EQ(set_mode(INT_MODE), INT_MODE); }

TEST(ModeGetter, GetInt)
{
    set_mode(INT_MODE);
    EXPECT_EQ(get_mode(), INT_MODE);
}

TEST(GlobalPosSetter, Set) { EXPECT_EQ(set_global_pos(100), 100); }

TEST(GlobalPosGetter, Get)
{
    set_global_pos(100);
    EXPECT_EQ(get_global_pos(), 100);
}

// Tests for valid characters
TEST(ValidCharTest, AllValidCharacters)
{
    // digits
    for (char c = '0'; c <= '9'; ++c) {
        EXPECT_TRUE(is_valid_char(c));
    }

    // operators
    const char* operators = "()*+-/";
    for (const char* op = operators; *op; ++op) {
        EXPECT_TRUE(is_valid_char(*op));
    }

    // whitespaces
    char whitespaces[] = {' ', '\t', '\n', '\r'};
    for (char ws : whitespaces) {
        EXPECT_TRUE(is_valid_char(ws));
    }
}

TEST(InvalidCharTest, InvalidCharacters)
{
    const char* invalid = "abcABC!@#$%^&_=<>?\"'";
    for (const char* c = invalid; *c; ++c) {
        EXPECT_FALSE(is_valid_char(*c));
    }
}

// Tests for validation and strip of input buffer
TEST(InputValidationDeathTest, ExitOnInvalidCharacters)
{
    char buffer[] = "9- 39  93084 cd";
    EXPECT_EXIT(validate_and_strip_input(buffer), ::testing::ExitedWithCode(3), "");
}

TEST(InputValidationAndStripTest, HandleValidInput)
{
    char buffer[] = " 12\t+\n34\r";
    char expected[] = "12+34";
    validate_and_strip_input(buffer);
    EXPECT_STREQ(buffer, expected);
}

TEST(InputValidationTest, HandleEdgeCases)
{
    // Mixed valid characters with whitespace
    {
        char buffer[] = " \t1\n+\r2*\t3 \n";
        validate_and_strip_input(buffer);
        EXPECT_STREQ(buffer, "1+2*3");
    }

    // Only operators and whitespace
    {
        char buffer[] = " + - \t* /\n";
        validate_and_strip_input(buffer);
        EXPECT_STREQ(buffer, "+-*/");
    }
}

// Tests for get_operand
TEST(GetOperand, GetIntNum)
{
    char buff[] = "2";
    set_global_pos(0);
    set_mode(INT_MODE);
    EXPECT_EQ(get_operand(buff).intValue, 2);
}

TEST(GetOperand, GetFloatNum)
{
    char buff[] = "2";
    set_global_pos(0);
    set_mode(FLOAT_MODE);
    EXPECT_NEAR(get_operand(buff).floatValue, 2.0, FLOAT_PRECISION);
}

TEST(GetOperand, GetIntSubExpression)
{
    char buff[] = "((2+4-1)/2)";
    set_global_pos(0);
    set_mode(INT_MODE);
    EXPECT_EQ(get_operand(buff).intValue, 2);
}

TEST(GetOperand, GetFloatSubExpression)
{
    char buff[] = "((2+4-1)/2)";
    set_global_pos(0);
    set_mode(FLOAT_MODE);
    EXPECT_NEAR(get_operand(buff).floatValue, 2.5000, FLOAT_PRECISION);
}

// Test for get_product
TEST(GetProduct, GetIntProduct)
{
    char buff[] = "2*2*3/6";
    set_global_pos(0);
    set_mode(INT_MODE);
    EXPECT_EQ(get_product(buff).intValue, 2);
}

TEST(GetProduct, GetFloatProduct)
{
    char buff[] = "2*2*3/5";
    set_global_pos(0);
    set_mode(FLOAT_MODE);
    EXPECT_NEAR(get_product(buff).floatValue, 2.4000, FLOAT_PRECISION);
}

// Tests for calculate_expressions
TEST(CalculateExpr, CalculateInt)
{
    char buff[] = "(5-4+1-1)*(5/2)";
    set_global_pos(0);
    set_mode(INT_MODE);
    EXPECT_EQ(calculate_expression(buff).intValue, 2);
}

TEST(CalculateExpr, CalculateFloat)
{
    char buff[] = "(5-4+1-1)*(5/2)";
    set_global_pos(0);
    set_mode(FLOAT_MODE);
    EXPECT_NEAR(calculate_expression(buff).floatValue, 2.5, FLOAT_PRECISION);
}

int main(int argc, char** argv)
{
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
