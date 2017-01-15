;minimal music player
;
;Copyright (C) 2014  jmimu (jmimu@free.fr)
;
;This program is free software: you can redistribute it and/or modify
;it under the terms of the GNU General Public License as published by
;the Free Software Foundation, either version 3 of the License, or
;(at your option) any later version.
;
;This program is distributed in the hope that it will be useful,
;but WITHOUT ANY WARRANTY; without even the implied warranty of
;MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;GNU General Public License for more details.
;
;You should have received a copy of the GNU General Public License
;along with this program.  If not, see <http://www.gnu.org/licenses/>.
;==============================================================


;==============================================================
; WLA-DX banking setup
; Note that this is a frame 2-only setup, allowing large data
; chunks in the first 32KB.
;==============================================================
.memorymap
   defaultslot 0
   ; ROM area
   slotsize        $8000
   slot            0       $0000
   slotsize        $4000
   slot            1       $8000
   ; RAM area
   slotsize        $2000
   slot            2       $C000
   slot            3       $E000
.endme

.rombankmap
   bankstotal 1
   banksize $8000
   banks 1
.endro


;==============================================================
; constants
;==============================================================


;==============================================================
; RAM section
;==============================================================
.ramsection "variables" slot 2
new_frame                     db ; 0: no; 1: yes
PauseFlag db ;1 if pause
;music
music1_start_ptr         dw ;pointer
music1_current_ptr         dw ;pointer
music1_tone_duration         db ;when 0 got to next tone
music1_current_tone         dw ;value (for debug)
music2_start_ptr         dw ;pointer
music2_current_ptr         dw ;pointer
music2_tone_duration         db ;when 0 got to next tone
music2_current_tone         dw ;value (for debug)
music3_start_ptr         dw ;pointer
music3_current_ptr         dw ;pointer
music3_tone_duration         db ;when 0 got to next tone
music3_current_tone         dw ;value (for debug)
drum_start_ptr         dw ;pointer
drum_current_ptr         dw ;pointer
drum_tone_duration         db ;when 0 got to next tone
drum_current_tone         db ;value (for debug)
.ends


;==============================================================
; SDSC tag and SMS rom header
;==============================================================
.sdsctag 1.2,"jmimu music player","Simple music player","jmimu"

.bank 0 slot 0
.org $0000
;==============================================================
; Boot section
;==============================================================
    di              ; disable interrupts
    im 1            ; Interrupt mode 1
    jp main         ; jump to main program


.org $0038
;==============================================================
; Vertical Blank interrupt
;==============================================================
    push af
      in a,($bf);clears the interrupt request line from the VDP chip and provides VDP information
      ;do something only if vblank (we have only vblank interrupt, so nothing to do)     
      ld a,1
      ld (new_frame),a
    pop af
    ei ;re-enable interrupt
    reti


.org $0066
;==============================================================
; Pause button handler
;==============================================================
    call CutAllSound
    
    ld a,(PauseFlag) ;taken from Heliophobe's SMS Tetris 
    xor $1  ;Just a quick toggle
    ld (PauseFlag),a
  retn


;inclusions
.include "init.inc"
.include "sound.inc"


;==============================================================
; Main program
;==============================================================
main:
    ld sp, $dff0 ;where stack ends ;$dff0
    
    ld a,0
    ld (PauseFlag),a

    ;==============================================================
    ; Set up VDP registers
    ;==============================================================
    call initVDP

    ;music init
    ;ld hl,Music1_start;data1 start in hl
    ;call InitMusic1
    ;ld hl,Music2_start;data2 start in hl
    ;call InitMusic2
    
    ld hl,test1_start	
    call InitMusic1
    ld hl,test2_start
    call InitMusic2
    ld hl,test3_start
    call InitMusic3
    ld hl,drums1_start
    call InitDrum


game_start:
    call CutAllSound


  
    ;disable interrupts and turn off screen before writing to it. Will it fix tiles issues?
    di  ; disable interrupts
    ; Turn screen off
    ld a,%10100000
;          |||| |`- Zoomed sprites -> 16x16 pixels
;          |||| `-- Doubled sprites -> 2 tiles per sprite, 8x16
;          |||`---- 30 row/240 line mode
;          ||`----- 28 row/224 line mode
;          |`------ VBlank interrupts
;          `------- Disable display
    out ($bf),a
    ld a,$81
    out ($bf),a
    
    ;==============================================================
    ; Clear VRAM
    ;==============================================================
    ; 1. Set VRAM write address to 0 by outputting $4000 ORed with $0000
    ld a,$00
    out ($bf),a
    ld a,$40
    out ($bf),a
    ; 2. Output 16KB of zeroes
    ld bc, $4000    ; Counter for 16KB of VRAM
    -:
        ld a,$00    ; Value to write
        out ($be),a ; Output to VRAM address, which is auto-incremented after each write
        dec bc
        ld a,b
        or c
        jp nz,-


        
    ; Turn screen on
    ld a,%11100000
;          |||| |`- Zoomed sprites -> 16x16 pixels
;          |||| `-- Doubled sprites -> 2 tiles per sprite, 8x16
;          |||`---- 30 row/240 line mode
;          ||`----- 28 row/224 line mode
;          |`------ VBlank interrupts
;          `------- Enable display
    out ($bf),a
    ld a,$81
    out ($bf),a

    ei  ; enable interrupts
    
    

MainLoop:

    ld a,(PauseFlag)
    cp 1
    jr z,MainLoop ;if pause do nothing in main loop
    

    call WaitForVBlank
    call PSGMOD_Play
    
   
    
    jp MainLoop
    




WaitForVBlank:
    push af
    -:
      ld a,(new_frame)
      cp 0
      jr z,-

      ld a,0
      ld (new_frame),a      
    pop af    
    ret   

PSGMOD_Play:
    ;~ ld c,0;channel in c*%100000(max 3*%100000)
    ;~ ld hl,(posY) ;Tone in hl (max 1024)
    ;~ ;ld l,h
    ;~ ;ld h,%00000011
    ;~ 
    ;~ ld a,h
    ;~ ;neg
    ;~ ld l,a
    ;~ ld h,%00000010
    ;~ 
    ;~ 
    ;~ call PlayTone
    ;~ 
    
    ;play harmonics or not depending on level number
    ;ld a,(current_level)
    ;and %00000001
    ;jr z,+
    ;call PlayMusicH
    ;ret
    ;+:

    call PlayMusic1
    call PlayMusic2
    call PlayMusic3
    ;call PlayDrum
    
    ;ld a,%11100000
    ;out ($7f),a
    ;ld a,%00000010
    ;out ($7f),a
    
        ;noise!
        ;ld c,%01100000;channel in c*%100000(max 3*%100000)
        ;call EnableChannel
        ;ld a,%00001000
        ;call PlayNoise0
        
    ret
    

;==============================================================
; Data
;==============================================================




