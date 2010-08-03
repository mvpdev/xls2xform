#!/bin/bash
# copy all forms in this folder over to emulator and start emulator
sudo mount -o loop ~/.android/avd/my_avd.avd/sdcard.img /media/sdcard
sudo cp *.xml /media/sdcard/odk/forms/
sudo umount /media/sdcard/
~/files/work/ODK/android-sdk-linux_86/tools/emulator -avd my_avd &

# http://blog.jayway.com/2009/04/22/working-with-sd-cards-in-the-android-emulator/