@ECHO OFF
@REM Run this from the top-level source directory, i.e. as windows\build.bat
RMDIR /S /Q build dist
DEL /Q frescobaldi.spec
py -m PyInstaller frescobaldi -D -w ^
	-n frescobaldi ^
	--collect-all frescobaldi_app ^
	--collect-all qpageview ^
	--collect-all ly ^
	--hidden-import pygame.pypm ^
	-i frescobaldi_app\icons\frescobaldi.ico
