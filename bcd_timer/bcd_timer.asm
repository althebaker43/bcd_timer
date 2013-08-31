/*
 * bcd_timer.asm
 *
 *  Created: 7/22/2013 8:07:40 PM
 *   Author: Allen
 */ 

// BEGIN CONSTANTS

// 7-segment LED driver pins
.SET    SEG7 = PORTD
.SET    SEG7_A = PORTD0
.SET    SEG7_B = PORTD1
.SET    SEG7_C = PORTD2
.SET    SEG7_D = PORTD3

// Timer constants
.SET    WAIT_260MS = 0XFF   // 260 milliseconds

// END CONSTANTS


// BEGIN SETUP

    // Set Reset Interrupt vector
.ORG        0X0000
    RJMP    RESET

.ORG        0X0034

RESET:

    // Setup stack pointer
    LDI     R16,LOW(RAMEND)
    LDI     R17,HIGH(RAMEND)
    OUT     SPL,R16
    OUT     SPH,R17

    // Setup Port D
    LDI     R16,0X0F        // Set low nibble of R16 high
    OUT     DDRD,R16        // Set PD0-PD3 to output

    // Disable power reduction for Timer 2
    LDI     XL,LOW(PRR)     // Move low byte of PRR into XL
    LDI     XH,HIGH(PRR)    // Move high byte of PRR into XH
    LD      R16,X           // Load PRR contents into R16
    CBR     R16,0X40        // Clear Timer 2 bit
    ST      X,R16           // Store new flags into PRR

    // Configure Timer 2
    //  Disable waveform generation
    //  Set clock source to internal I/O clock
    //  Prescaler set to divide freq. by 1024
    CLR     R16             // Clear R16
    LDI     XL,LOW(TCCR2A)  // Load low byte of TCCR2A into XL
    LDI     XH,HIGH(TCCR2A) // Load high byte of TCCR2A into XH
    ST      X+,R16          // Clear TCCR2A and increment X
    LDI     R16,0X07        // Set [2:0] in R16
    ST      X,R16           // Set CS2[2:0] in TCCR2B

    // Disable all Timer 2 interrupts
    LDI     XL,LOW(TIMSK2)  // Load low byte of TIMSK2 into XL
    LDI     XH,HIGH(TIMSK2) // Load high byte of TIMSK2 into XH
    CLR     R16             // Clear R16
    ST      X,R17           // Clear TIMSK2

    // Initialize timer interval
    LDI     R24,WAIT_260MS

    // Initialize 7-segment output to 1
    LDI     R21,1

// END SETUP


// BEGIN MAIN PROGRAM

MAIN:

    CALL    WAIT        // Wait for a certain amount of time

    OUT     SEG7,R21    // Output current value to 7-segment pins

    INC     R21         // Increment 7-segment value
    CPI     R21,10      // Compare new value with 10
    BRLO    MAIN        // If less than, loop back to MAIN
    
    CLR     R21         // Else, set R21 back to zero
    RJMP    MAIN        // Loop back to MAIN

// END MAIN PROGRAM


// BEGIN FUNCTIONS

// Name: WAIT
// Descr: Waits for a specified period
// Inputs: 
//  R24: Interval constant
WAIT:
    
    // Store interval constant in output compare register
    LDI     XL,LOW(OCR2A)   // Load low byte of OCR2A into XL
    LDI     XH,HIGH(OCR2A)  // Load high byte of OCR2A into XH
    ST      X,R24          // Store constant in OCR2A and decrement X

    // Clear output compare A flag
    SBI     TIFR2,OCF2A     // Cleared by writing 1 to location

    // Reset Timer 2
    CLR     R16     // Clear R16
    ST      -X,R16  // Decrement X to TCNT2 and clear it

    // Wait for Timer 2 output compare flag
WAIT_T2:

    SBIS    TIFR2,OCF2A // Check output compare A flag
    RJMP    WAIT_T2     // If still cleared, jump back to WAIT_T2

    RET // Else, return from WAIT

// END FUNCTIONS