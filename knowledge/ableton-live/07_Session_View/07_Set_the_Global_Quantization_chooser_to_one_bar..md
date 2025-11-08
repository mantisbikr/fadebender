---
id: 07
title: "Set the Global Quantization chooser to one bar."
chapter: 07
---
# 7 Set the Global Quantization chooser to one bar.

7.

Set the Global Quantization chooser to one bar.
To automatically quantize the notes you are about to record, choose an appropriate value for
Record Quantization.
Double-click any of the Session View slots in the desired MIDI track (the one containing the
Impulse or other instrument). A new, empty clip will appear in the slot. The new clip will default
to a loop length of one bar, but you can change that by double-clicking the clip and changing
its loop properties.
Arm the track.
Press the Session Record button.
The notes you play are added into the looping clip, and you can observe your recording in the
Clip View.
The clip overdubs as it loops, allowing you to build your pattern layer by layer. However, if you
would like to pause recording for a moment to rehearse, you can deactivate overdubbing by
pressing the Session Record button again. The contents of the clip will continue to play, but you
can play along without being recorded. When you are ready to record again, press the Session
Record button once again. Subsequent presses of the Session Record button will toggle
between playback and overdub.

Note that holding Alt (Win) / Option (Mac) while double-clicking the empty slot to create a
new clip will implicitly arm the track and launch the clip.

At any time while overdub recording is going on, you can use the Undo command to remove the last
take, or even draw, move or delete notes in the Clip View’s MIDI Note Editor.

19.3.4 MIDI Step Recording

The MIDI Editor allows you to record notes with the transport stopped by holding down keys on your
controller or computer MIDI keyboard and advancing the insert marker according to the grid settings.
This process, known as step recording, allows you to enter notes at your own pace, without needing to
listen to a metronome or guide track.

Step Recording in the MIDI Editor.

1.
2.
3.

Arm the MIDI track that contains the clip into which you want to record.
Enable the Preview switch in the clip’s MIDI Editor.
Click in the MIDI Editor to place the insert marker at the position where you want to begin
recording.

Pressing the right arrow key on your computer keyboard will move the insert marker to the right,
according to the grid settings. Any notes that are held down as you press the right arrow key will be
added to the clip. If you continue holding notes as you press the right arrow key again, you will
extend their duration. To delete notes that you’ve just recorded, keep them depressed and press the
left arrow key.

The step recording navigators can also be MIDI mapped.

19.4 Recording in Sync

Live keeps the audio and MIDI you have recorded in sync, even when you later decide on a different
song tempo. In fact, Live allows you to change the tempo at any time before, after and even during

recording. You could, for instance, cheat a bit by turning down the tempo to record a technically
difficult part, and pull it up again afterwards.

It is important to record in sync to make sure everything will later play in sync.

The Metronome Switch.

The easiest way to record in sync is to play along with or to use the built-in metronome, which is
activated via its Control Bar switch and will begin ticking when the Play button is pressed or a clip is
launched.

The Preview Volume Knob.

To adjust the metronome volume, use the mixer’s Preview Volume knob. Further metronome settings
can be adjusted via the pull-down menu next to the metronome switch.

Notice that Live’s metrical interpretation of the material in a clip can be edited, at any time, using
Warp Markers. Warp Markers can be used to fix timing errors and to change the groove or feel of
your audio or MIDI recordings. Using Warp Markers, you can fix things that would otherwise require
complicated editing or could not be done at all.

19.4.1 Metronome Settings

You can access the Metronome Settings menu via the pull-down switch next to the metronome, or by
opening the context menu for the metronome itself.

The menu lets you set the count-in length for recording. You can also change the sound of the
metronome’s tick.

The Rhythm settings allow you to set the beat division at which the metronome ticks. With the default
“Auto” setting, the tick interval follows the time signature’s denominator. Beat divisions that do not fit
into one bar of the current time signature will appear disabled.

If the currently selected beat division no longer fits in a bar due to a time signature change, the
metronome’s tick will revert to the “Auto” setting. However, if the time signature is changed in a way
that makes the beat division fit in a bar again, the tick will revert to following the selected beat
division.

When Enable Only While Recording is checked and the metronome is activated, the metronome will
be highlighted while transport is running, but will only be audible while recording. If you are recording
into the Arrangement while the Punch-In switch is active, the metronome will only be audible after the
punch-in point.

19.5 Recording Quantized MIDI Notes

If you will be recording MIDI, you have the option of automatically quantizing MIDI notes while
recording. The Record Quantization chooser in the Edit menu allows selecting the meter subdivisions
with which your recorded notes will align. When recording into the Arrangement, record quantization
is an independent step in Live’s Undo history. This means that if, for example, you recorded with
Record Quantization set to “Eighth Note Triplet Quantization“ and then changed your mind, using the
Edit menu’s Undo command would undo only the quantization and leave your recording otherwise
intact.

For Session and Arrangement recording, the Record Quantization setting cannot be changed mid-
recording.

When overdub recording with the Clip View Loop activated, changes to the Record Quantization take
effect immediately, and they cannot be separately undone with the Edit menu command.

Recorded MIDI notes can also be quantized post-recording with the Edit menu’s Quantize command,
as described in the chapter on editing MIDI.

19.6 Recording with Count-in

A count-in for recording can be set via the pull-down menu next to the Metronome switch. When set
to any value other than “None,“ Live will not begin recording until the count-in is complete. The
Arrangement Position fields in the Control Bar display the count-in in blue as bars-beats-sixteenths.

The Count-In is Displayed in the Control Bar.

The count-in runs from negative bars-beats-sixteenths (beginning at -2.1.1., for example, with a Count-
In setting of 2 bars) up to 1.1.1., at which point recording commences.

19.7 Setting up File Types

The following Settings from the Record, Warp & Launch tab are relevant to the sample files that are
created by recording:

•

•

The sample file type you would like Live to create can be chosen from the File Type chooser in
the Record, Warp & Launch Settings.
The bit depth of the sample file you will create by recording can be chosen from the Bit Depth
chooser in the Record, Warp & Launch Settings.

You can save time by setting up reasonable defaults for the clips you are recording in the Record,
Warp & Launch Settings tab. In particular, it is smart to indicate the rough category of sound to be
recorded by choosing the appropriate default Warp Mode. If you decide later on a different song
tempo, the program will automatically maintain good sound quality, usually without further
adjustment.

19.8 Where are the Recorded Samples?

Recorded samples are stored with the current Set’s Project folder, under Samples/Recorded. Until the
Set is saved, it remains at the location specified by the Temporary Folder preference which is found in
the Settings’ File/Folder tab. To make sure Live will not run out of disk space while recording into a
new Set, please make sure the Temporary Folder is on a drive/partition with sufficient free space.

19.9 Using Remote Control for Recording

Using Key Map Mode and MIDI Map Mode, you can operate Live’s recording functions without
using the mouse.

You can map the Control Bar’s Arrangement Record and transport controls as well as the track Arm
buttons. For recording into the Session slots, you can map the Session Record and New buttons, the
individual slots, and the relative navigation controls to initiate recording remotely; for instance:

The Scene Up/Down Buttons.

One key is used to jump to the next scene…

A Track Launch Button.

… and another key to start and end recording in the respective track.

You can also map the step recording navigators.

The Step Recording Arrows.

This allows you to, for example, use MIDI foot pedals to move the clip’s insert marker, thereby keeping
both hands free for playing a keyboard.

19.10 Capturing MIDI

Live is always listening to MIDI input on armed or input-monitored tracks, and Capture MIDI lets you
retrieve the material you’ve just played on those tracks. This is particularly useful if you forgot to press

the Record button before playing, or if you prefer to improvise or experiment freely without the stress
of recording.

The Capture MIDI Button in the Control Bar.

To capture the MIDI notes you just played, press the Capture MIDI button.

On Push 1 or Push 2, you can trigger Capture MIDI by holding the Record button and pressing the
New button. On Push 3, you can use the dedicated Capture button.

Capture MIDI behaves differently depending on the state of the Live Set. We will look at these
different behaviors below.

19.10.1 Starting a New Live Set

If the Live Set contains no other clips and the transport is stopped:

•

•

•

•

A new clip containing the phrase you played will be created on every monitored MIDI track.
Note that Capture MIDI will only add clips to the Session or Arrangement View, depending on
which View is currently in focus.
Capture MIDI will detect and adjust the song tempo, set appropriate loop boundaries and
place the played notes on the grid. Note that Capture MIDI’s tempo detection will set the
tempo in the 80-160 BPM range. If you consider the played material to be at a tempo outside
this range, you can adjust the song tempo to your liking. To help Capture MIDI detect a phrase
correctly, it is recommended to end playing on the first beat (or “downbeat”) of the next bar.
Live’s transport will immediately begin to run, and play back the captured loop. This allows you
to create overdubs if you wish (for more information about overdubbing with Capture MIDI,
refer to the section Adding Material to an Existing Live Set below).
All of your played material will be saved in the clip, and any notes that you played before the
detected phrase will appear prior to the clip start marker. This enables you to adjust the start/
end or loop markers to set a different loop. To discard unwanted material outside the set loop,
simply right-click on the clip and select the Crop Clip command.

Note: If only one note is played in the first captured MIDI clip, the loop boundaries are set to the note
start and end, and the tempo is accordingly calculated, resulting in a one, two, four, or eight bar loop.
This is particularly useful when playing a rhythmical sample with a single MIDI note.

19.10.2 Adding Material to an Existing Live Set

If Live’s transport is running, there are already other clips in the Live Set, or the tempo is automated:

•

•

•

Capture MIDI will not detect or adjust the song tempo. Instead, Capture MIDI will use the
existing tempo to detect a meaningful musical phrase from your played material and create a
loop.
While the transport is running, you can “play along” with other clips. You can also use Capture
MIDI to “overdub” a playing clip, by playing over it on the same track. Pressing the Capture
MIDI button will add the material you just played on top of the existing clip’s content, allowing
you to build your pattern layer by layer.
All of your played material will be saved in the clip, and any notes that you played before the
detected phrase will appear prior to the clip start marker. This allows you to adjust the start/
end or loop markers to set a different loop.

20. Comping

Comping makes it possible to pick the best moments of each recorded performance, and combine
them into a composite track (also known as a “comp”). Live can create and organize individual takes
from your recorded material, allowing you to piece your favorite parts together. You can store
alternative versions of a clip arrangement on multiple take lanes. You can also drag samples from
your library onto take lanes and use comping as a creative sample-chopping tool.

20.1 Take Lanes

Every audio or MIDI track in the Arrangement View may consist of multiple parallel lanes. The first
lane of a track is the main lane, which is always available and is audible by default. A track can also
contain an arbitrary number of take lanes, which serve as a container for clips that were recorded or
manually added to them. Take lanes are never audible, unless Audition Mode is enabled.

A Track’s Main Lane (Above) and Its Take Lanes (Below).

Take lanes are automatically created when recording new clips in the Arrangement, and they can also
be inserted manually. You can toggle the visibility of take lanes by choosing Show Take Lanes from a
track header’s context menu, or using the Ctrl
keyboard shortcut. Note that this only toggles the visibility of existing take lanes. Take lanes are not
visible when Automation Mode is enabled. You can use the left arrow key to navigate from a take
lane to the main track, this will fold all take lanes as well.

U (Win) / Cmd

U (Mac)

Option

Alt

20.2 Inserting and Managing Take Lanes

You can manually insert a take lane into one or multiple selected tracks, via the Insert Take Lane entry
in the Create menu or a track/take lane header’s context menu, or using the Shift
(Win) / Shift
show all take lanes, if they were not already visible.

T (Mac) keyboard shortcut. Inserting a take lane will also immediately

Option

Alt

T

Selected take lanes can be duplicated using the keyboard shortcuts Ctrl
(Mac), or by right-clicking on the take lane header and selecting “Duplicate.” You can delete selected
take lanes using the Backspace or Delete key, or via the Delete command in the Edit menu.

D (Win) / Cmd

D

Selected take lanes can be resized vertically by pressing Alt
Alt

- (Win) / Option

- (Mac), or by pressing Alt (Win) / Option (Mac) while using the

+ (Win) / Option

+ (Mac) or

mousewheel. Multiple selected take lanes can be resized by dragging the resize handles with the
mouse. When holding the Alt (Win) / Option (Mac) modifier, all selected take lanes are resized
simultaneously, similar to tracks.

You can reorder selected take lanes within their track by dragging and dropping them. You can also
move take lanes using the Ctrl (Win) / Cmd (Mac) modifier with the up or down arrow key.

Take lanes can be renamed in the same way as tracks, using the Rename command in the Edit menu
or a take lane header’s context menu, or using the Ctrl
shortcut. Multiple selected take lanes can also be renamed simultaneously. Using the Tab and
Shift

Tab keyboard shortcuts lets you quickly move between lanes and tracks while renaming

R (Mac) keyboard

R (Win) / Cmd

them.

20.3 Recording Takes

While recording new clips in the Arrangement View, take lanes are automatically added to armed
audio and MIDI tracks, and clips are created within those take lanes.

Recording over existing clips, either by recording individual passes or by recording in a loop, will add
a new take lane for each pass. Existing take lanes will be automatically reused when no other clip
exists after the punch-in point.

The last recorded clip in a track is always copied to that track’s main lane, so that it becomes
immediately audible when playing back the Set.

Note that recorded clips inherit their track’s color by default. You can configure Live to automatically
assign a different color to each take, by setting the Clip Color toggle to Random in the Theme &
Colors Settings.

20.4 Inserting Samples

You can drag samples and MIDI files to take lanes from the browser or Finder/File Explorer. When
multiple samples are selected, pressing the Ctrl (Win) / Cmd (Mac) modifier key and dragging
will insert each sample into sequential tracks and/or take lanes.

20.5 Auditioning Take Lanes

You can audition a take lane by clicking the Audition Take Lane button (displayed as a speaker icon)
in that take lane’s header, or using the T keyboard shortcut.

The Audition Take Lane Button.

Note that while you can audition take lanes from different tracks at the same time, you can only
audition one take lane per track. If the time selection or lane header selection stretches across multiple
lanes on the same track, the last selected lane will be auditioned.

20.6 Creating a Comp

Selected material in take lanes can be copied to the main lane by pressing the Enter key or via a
take lane’s Copy Selection to Main Lane context menu command.

It is possible to replace clips in a track’s main lane with the next or previous take lane clip by selecting
a clip header, or by making a time selection on a track’s main lane or take lane, and then pressing
Ctrl (Win) / Cmd (Mac) with the up or down arrow key. If the time selection is on a take lane, it
switches to the next or previous take. Note that empty take lanes are ignored.

Replacing Part of a Clip with Content from a Different Take Lane.

In Draw Mode, selected take lane material can be copied to a track’s main lane in one single gesture
by clicking, dragging and then releasing the mouse. It is also possible to quickly cycle between takes
within a time selection by single-clicking on a take lane and immediately releasing the mouse.

Note that clips copied to a track’s main lane are independent copies of take lane clips. This means
that you can freely edit clips in a track’s main lane without modifying or fragmenting the original take
lane clips, and vice versa. Also note that clips in take lanes can be edited the same way as other clips
in the Arrangement View, e.g., they can be moved, copied/pasted, dragged/dropped, consolidated,
cropped, or duplicated. They can also be copied to Session View clip slots by either copying and
pasting or dragging and dropping.

You can prevent clicks between adjacent clips by enabling the Create Fades on Clip Edges option in
the Record, Warp & Launch Settings. Live will automatically create four-millisecond crossfades
between adjacent clips. You can also manually create these crossfades by selecting multiple clips and
pressing Ctrl

F (Win) / Cmd

F (Mac).

Option

Alt

20.7 Source Highlights

For every Arrangement clip, Live will highlight its source material in a take lane by displaying it in full
color, while dimming all unused take lane material. This makes it easier to track the recorded material
that the clip originally came from. Note that source highlights will only be shown when the clips have
matching positions and properties.

A Clip’s Source Material Highlighted in a Take Lane.

Source highlights on take lanes can be resized to adjust the split point between two adjacent parts of
a comp by dragging the edge of the highlight.

Drag to Adjust the Split Point Between Two Adjacent Parts of a Comp.

21. Working with Instruments and
Effects

Every track in Live can host a number of devices. These devices can be of three different sorts:

•
•

•

MIDI effects act upon MIDI signals and can only be placed in MIDI tracks.
Audio effects act upon audio signals and can be placed in audio tracks. They can also be
placed in MIDI tracks as long as they are “downstream“ from an instrument.
Instruments are devices that reside in MIDI tracks, receive MIDI and output audio.

The Device View is where you insert, view and adjust the devices for the selected track. To select a
track and open the Device View to access its devices, double-click the track’s name. The Device View
appears in the bottom area of the Live screen.

Devices in the Device View.

To save space in the Device View, a device can be collapsed by double-clicking on its title bar or by
choosing Fold from the title bar’s context menu.

Devices Can Be Folded.

To learn about a particular device and how to operate it, consult the Live Audio Effect Reference, Live
MIDI Effect Reference, or Live Instrument Reference chapters.

To learn about creating and using custom groupings of instruments and effects, check out the
Instrument, Drum and Effect Racks chapter.

Get “hands-on“ with devices by assigning their parameters to MIDI or key remote control.

21.1 Using the Live Devices

Devices in Live’s Browser.

Live’s built-in devices can be accessed in the browser. You will notice that Live’s Synths, Audio Effects,
and MIDI Effects each have their own labels in the browser’s sidebar.

The easiest way to place a device in a track is to double-click on it in the browser, which creates a
new track to hold the device. Alternatively, select a destination track by clicking within it, then select a
device or preset in the browser and press Enter to add it to the selected track.

You can also drag devices into tracks or drop areas in the Session and Arrangement Views, or into the
Device View. Dragging a sample to the Device View of a MIDI track creates a Simpler instrument with
this sample loaded.

Note: If you are using an external input signal to feed your Live track using the default settings, the
track’s Arm button in the mixer must be activated in order to hear the input through the devices in your
track’s device chain. On MIDI tracks, this is normally activated automatically when inserting an
instrument.

MIDI and Audio Track Arm Buttons.

This is how you would play live instruments through effects on a track, for example, or use a MIDI
keyboard’s input to play a track’s instrument. Note that you can easily move from this setup into
recording new clips for further use in Live. If you have alternative monitoring preferences, please see
the Monitoring section to learn how to make these settings.

To add another device to the track, simply drag it there or double-click its name to append it to the
device chain. Signals in a device chain always travel from left to right.

You can drop audio effects in at any point in an audio track’s device chain, keeping in mind that the
order of effects determines the resulting sound. The same is true for a MIDI track’s device chain.

If you drop an instrument into a MIDI track’s device chain, be aware that signals following (to the right
of) the instrument are audio signals, available only to audio effects. Signals preceding (to the left of)
the instrument are MIDI signals, available only to MIDI effects. This means that it’s possible for a MIDI
track’s device chain to hold all three types of devices: first MIDI effects, then an instrument, and finally
audio effects.

A MIDI Track’s Device Chain Can Contain All Three Device Types.

To remove a device from the chain, click on its title bar and press your computer’s Backspace or
Delete key, or select Delete from the Edit menu. To change the order of devices, drag a device by
its title bar and drop it next to any of the other devices in the Device View. Devices can be moved to
other tracks entirely by dragging them from the Device View into the Session or Arrangement Views.

Edit menu commands such as cut, copy, paste and duplicate can be used on devices. Pasted devices
are inserted in front of the selected device. You can paste at the end of a device chain by clicking in
the space after the last device, or by using the right arrow key to move the selection there. Generally,
devices can be placed, reordered and deleted without interrupting the audio stream.

Device Activator Switches.

Devices are turned on and off using their Activator switches. Turning a device off is like temporarily
deleting it: The signal remains unprocessed, and the device does not consume CPU cycles. Live
devices generally do not load down the CPU unless they are active. For more information, please
refer to the CPU load section. The Freeze Track command discussed there is especially helpful when
working with CPU-intensive devices.

Devices in Live’s tracks have input and output level meters. These meters are helpful in finding
problematic devices in the device chain: Low or absent signals will be revealed by the level meters,
and relevant device settings can then be adjusted, or the device can be turned off or removed.

The Level Meters Between Devices in a Chain.

Note that no clipping can occur between devices because there is practically unlimited headroom.
Clipping can occur when an overly strong signal is sent to a physical output or written to a sample
file.

Further information about track types in Live can be found in the Routing and I/O chapter, including
information on using return tracks to distribute the effect of a single device amongst several tracks.
After reading about using devices in Live, it might also be interesting to look into clip envelopes, which
can automate or modulate individual device parameters on a per-clip basis.

21.1.1 Live Device Presets

Every Live device can store and retrieve their parameter settings as presets. Each device appears in
the content pane of the browser as a folder that can be opened to reveal its presets.

Presets in the Browser.

You can browse and load presets quickly with the computer keyboard:

•
•
•

Scroll up and down using the up and down arrow keys.
Close and open device folders using the left and right arrow keys.
Press Enter to load a device or preset.

Pressing Q or clicking a device’s Hot-Swap Presets button will temporarily link the browser to a
device and reveal its presets. With the device and browser linked in this manner, you can quickly
browse and audition different presets. In Hot-Swap Mode, devices and presets are loaded
automatically upon selection in the browser. To load a device’s default factory settings, select the
parent folder of its presets (i.e., the one with the device’s name) from the browser.

Note that pressing Q to enter Hot-Swap mode will swap from the last selected device on a given
track. If no device was selected, swap will be enabled from the first audio effect (on audio tracks) or
the instrument (on MIDI tracks).

The Hot-Swap Presets Button.

The link between the browser and the device will be broken if a different view is selected, or if the Q
key or the Hot-Swap button is pressed again. Preset hot-swapping can also be cancelled with a press
of the Esc key or by pressing the close button in the Hot-Swap bar at the top of the browser.

Note that although importing via the browser is the recommended method, presets can also be
dropped directly into Live from the Explorer (Win) / Finder (Mac).

21.1.1.1 Saving Presets

You can create and save any number of your own presets in the browser’s User Library.

The Save Preset Button.

Click the Save Preset button to save a device’s current settings (including any custom info text) as a
new preset. You will be redirected to the browser, where you can press Enter to use Live’s
suggested name, or you can type one of your own. To cancel preset saving, press the Esc key. You
can also save presets to specific folders in the Places section of the browser (such as your Current
Project folder) by dragging from the title bar of the device and dropping into the browser location of
your choice.

For detailed information on what can be done with the browser, please see the Managing Files and
Sets chapter. For more on how to store project-specific presets, see the Projects and Presets section.

21.1.1.2 Default Presets

Presets saved to the Defaults folders in your User Library will load in place of the generic device
settings. There are also Defaults folders that allow you to:

•

•

•

Customize how Live responds to various user actions, such as sample dropping, slicing, and
converting audio to MIDI.
Cause newly-created MIDI and audio tracks to load with certain devices already in place,
complete with custom parameter settings.
Load VST and Audio Units plug-ins with a specific collection of parameters already configured
in Live’s panel.

The Default Presets folders in the User Library.

To save the current settings of a Live device as a default preset, open the context menu on the device’s
header and select “Save as Default Preset.“ This works for all of Live’s instruments, MIDI effects and
audio effects (including the various types of Racks). If you have already saved a default preset for a
particular device, Live will ask you before overwriting it.

To create a default configuration preset for a VST or Audio Unit plug-in:

•
•
•

Load the selected plug-in to a track.
From the plug-in’s Configure Mode, set up your desired collection of parameters.
Open the context menu on the track header and select “Save as Default Configuration.”

If you have both VST and Audio Units versions of a particular plug-in installed, you can create
separate default configuration presets for each type. Note that default presets for plug-ins do not save
the settings of the configured parameters; only the parameter configuration within Live’s panel is
saved.

To create default presets for MIDI and audio tracks:

•

•
•

Load the device(s) you would like as default onto a track (or no devices, if you would like your
default track to be empty).
Adjust the device parameters as you like.
Open the context menu on the track header and select “Save as Default Audio/MIDI Track.”

To specify how Live behaves when dragging a sample to a Drum Rack or the Device View of a MIDI
track:

•
•
•

Create an empty Simpler or Sampler.
Adjust the parameters as you like.
Drag the edited device to the “On Drum Rack“ or “On Device View“ folder, which can be
found in the Defaults/Dropping Samples folders in your User Library. Drum Rack pad defaults
can also be saved via a context menu option on a Drum Rack’s pad.

To adjust how Live behaves when slicing an audio file:

•
•
•
•
•
•

Create an empty Drum Rack.
Add an empty Simpler or Sampler to the Drum Rack to create a single chain.
Add any additional MIDI or Audio Effects to this chain.
Adjust parameters in any of the devices.
Assign Macro Controls to any of the controls in the chain’s devices.
Drag the entire Drum Rack to the Defaults/Slicing folder in your User Library.

You can create multiple slicing presets and choose between them in the Slicing Preset chooser in the
slicing dialog.

To create default presets for converting Drums, Harmony, or Melody to MIDI:

•

•
•
•
•

Create a MIDI track containing the instrument you would like to use as your default for a
particular conversion type. Note that default presets for converting drums must contain a Drum
Rack.
Add any additional MIDI or Audio Effects to the track.
Adjust parameters in any of the devices.
If you’re using multiple devices, group them to a Rack.
Drag the entire Rack to the appropriate folder in Defaults/Audio to MIDI in your User Library.

In addition to these program-wide default presets, you can also create default presets that are specific
to only one Project. This can be useful if, for example, you’re using specialized device or track
configurations for a particular Set, and would like to create variations of the Set which will also have
access to these presets, but without overwriting the more generalized default presets you use for your
other types of work. To create Project-specific default presets:

•
•

•

Recreate the Defaults folder and any desired subfolders within the Project folder.
Depending on which types of Project-specific defaults you’d like to work with, adjust the
corresponding device parameters, track settings, etc.
Save the device or track to the appropriate folder in your Project-specific Defaults folder.

Now, whenever you’ve loaded a Set from this Project, any default presets that you’ve saved into these
Project folders will be used instead of those found in the User Library. Note that the context menu
options for saving default presets will save them to your main User Library, and so cannot be used to
save Project-specific defaults.

21.2 Using Plug-Ins

The collection of devices that you can use in Live can be extended with plug-ins. Live supports
Steinberg Media’s VST plug-in format, as well as the Audio Units (AU) plug-in format (macOS only),
specifically:

•
•
•
•

VST2
VST3
Audio Units 2
Audio Units 3 (Live 11.2 and later)

Working with VST and Audio Units plug-Ins is very much like working with Live devices. VST and AU
instruments can only be placed in Live MIDI tracks and, like Live instruments, they will receive MIDI
and output audio signals. Plug-in audio effects can only be placed in audio tracks or following
instruments. Please see the previous section, Using the Live Devices, for details.

To skip plug-in scanning when Live is launched, hold the Alt (Win) / Option (Mac) modifier
when opening the program until the splash screen closes. This can be helpful when troubleshooting
crashes to see if any plug-ins are causing the problem.

Plug-Ins in the Browser.

Audio Units and VST plug-ins are browsed and imported using the browser’s Plug-Ins label. Plug-in
instruments can be differentiated from plug-in effects in the browser, as they appear with a keyboard
icon.

Note that plug-in presets are only available in the browser for Audio Units plug-ins. In some instances,
factory presets for Audio Units will only appear in the browser once the device has been placed in a
track and its Hot-Swap button activated.

Note: The first time you start Live, no plug-ins will appear in the Plug-Ins label as you must first
“activate“ your plug-in sources. Activating your plug-in sources tells Live which plug-ins you want to
use and where they are located on your computer. Information on activating (and deactivating) plug-
in sources can be found later in this chapter, in the sections on the VST Plug-In folder and Audio Units
Plug-Ins.

Note for “Intel® Mac“ users: Intel® Mac computers cannot natively run VST or AU plug-ins that have
been written for the PowerPC platform. Only plug-ins of type Universal or Intel® can be used in Live.

If you install/uninstall a plug-in while the program is running, Live will not detect your changes or
implement them in the browser until the next time you start the program. Use the Rescan button in the
Plug-Ins Settings to rescan your plug-ins while Live is running, so that newly installed devices become
immediately available in the browser.

You can also rescan if you believe that your plug-in database has somehow become corrupted.
Holding down the Alt (Win) / Option (Mac) modifier while pressing Rescan will delete your
plug-in database altogether and run a clean scan of your plug-ins.

21.2.1 Plug-Ins in the Device View

A VST Plug-In in the Device View.

Once a plug-in is dragged from the browser into a track, it will show up in the Device View. For plug-
ins with up to 64 modifiable parameters, a Live panel will represent all of the parameters as horizontal
sliders. Plug-ins that contain more than 64 parameters will open with an empty panel, which you can
then configure to show the parameters you want to access. The plug-in’s original interface can be
opened in a separate window.

The Plug-In Unfold Button.

You can view or hide the plug-in’s parameters by toggling the

 button in the plug-in’s title bar.

The X-Y control field can be used to control two plug-in parameters at once and is therefore especially
well-suited for live control. To assign any two plug-in parameters to the Live panel X-Y field, use the
drop-down menus directly beneath it.

21.2.1.1 Showing Plug-In Panels in Separate Windows

The Show/Hide Plug-In Window Button.

The Show/Hide Plug-In Window button opens a floating window that shows the original VST or
Audio Units plug-in panel. Changing parameters on the floating window has the same effect as
changing them in the Live panel, and vice versa.

There are a few important Plug-Ins Settings for working with plug-in windows:

•

•

•

If activated, the Auto-Open Plug-In Window Preference assures that plug-in windows open
automatically when plug-ins are loaded into tracks from the browser.
If the Multiple Plug-In Windows option in the Plug-In Settings is activated, you can open any
number of plug-in windows at once. Even with this option off, you can hold down the Ctrl
(Win) / Cmd (Mac) modifier when opening a new plug-in window to keep the previous
window(s) from closing.
Using the Auto-Hide Plug-In Windows preference, you can choose to have Live display only
those plug-in windows belonging to the track that is currently selected.

You can use the View menu’s Show/Hide Plug-In Windows command or the Ctrl
(Win) / Cmd
that the name of the track to which the plug-in belongs is displayed in the title bar of the plug-in
window.

P (Mac) shortcut to hide and show your open plug-in windows. Notice

Option

Alt

P

21.2.1.2 Plug-In Configure Mode

The Configure Button.

Configure Mode allows you to customize Live’s panel to show only the plug-in parameters that you
need to access. To do this:

•
•

Enter Configure Mode by pressing the “Configure“ button in the device’s header.
Click on a parameter in the plug-in window to add it to Live’s panel. For some plug-ins, it may
be necessary to actually change the parameter’s value. Additionally, certain plug-ins do not
“publish“ all of their parameters to Live. These parameters cannot be added to Live’s panel.

While in Configure Mode, parameters in Live’s panel can be reordered or moved by dragging and
dropping them to new locations. Parameters can be deleted by pressing the Delete key. If you try to
delete a parameter that has existing automation data, clip envelopes, or MIDI, key or Macro
mappings, Live will warn you before proceeding.

The parameters that you assign are unique for each instance of a given plug-in in your Set, and are
saved with the Set. If you would like to save a setup using a particular collection of parameters, you
can create a Rack containing the configured plug-in. Racks can then be saved to your User Library
and loaded into other Sets. You can also save a particular parameter configuration as a default
preset.

Certain plug-ins do not have their own windows, and instead only show their parameters in Live’s
panel. For these plug-ins, it is not possible to delete parameters when in Configure Mode (although
they can still be moved and reordered).

There are several ways to add plug-in parameters to Live’s panel without entering Configure Mode:

•

•

•

Adjusting a parameter in the plug-in’s floating window creates temporary entries for that
parameter in the clip envelope and automation choosers, as well as the choosers in the panel’s
X-Y field. These entries are removed when you adjust another parameter. To make the entry
permanent (thus adding it to Live’s panel), either edit the parameter’s automation or clip
envelope, select another parameter in the automation or clip envelope choosers or select the
temporary parameter in one of the X-Y field’s choosers.
When a parameter is changed on a plug-in’s floating window during recording, automation
data is recorded automatically. When recording is stopped, the automated parameters are
automatically added to Live’s panels for any plug-ins that were adjusted.
When in MIDI, key or Macro mapping mode, adjusting any parameter in the plug-in’s window
will create it in Live’s panel. The new panel entry will be automatically selected, allowing you to
map it immediately.

Once a plug-in is placed in a track and you have (optionally) configured its parameters in Live’s
panel, you can use it just like a Live device:

•
•

•
•

•

You can map MIDI controller messages to all of the parameters in Live’s panel.
You can drag or copy the device to different locations in the device chain or to other tracks,
according to the rules of audio effects and instruments.
You can automate or modulate its continuous parameters with clip envelopes.
You can use the multiple I/O features of some plug-ins by assigning them as sources or targets
in the routing setup of tracks. See the Routing and I/O chapter for details.
You can create custom info text for the plug-in.

21.2.2 Sidechain Parameters

Normally, the signal being processed and the input source that triggers the plug-in device are the
same signal. But by using sidechaining, it is possible to apply processing to a signal based on the
level of another signal. In plug-in devices that support sidechaining, you can access the sidechain
parameters on the left side of the device.

Plug-In Sidechain Parameters.

The choosers allow you to select any of Live’s internal routing points. This causes the selected source to
act as the device’s trigger, instead of the signal that is actually being processed.

The Gain knob adjusts the level of the external sidechain’s input, while the Mix knob allows you to use
a combination of sidechain and original signal as the trigger. With Mix at 100%, the device is
triggered entirely by the sidechain source. At 0%, the sidechain is effectively bypassed. Note that
increasing the gain does not increase the volume of the source signal in the mix. The sidechain audio is
only a trigger for the device and is never actually heard.

The Mute button allows you to listen to only the plug-in device’s output, bypassing the sidechain
source’s input.

21.3 VST Plug-Ins

21.3.1 The VST Plug-In Folder

When you start Live for the first time, you will need to activate your VST plug-in sources before
working with VST plug-ins. Depending on your computer platform, you may also have to tell Live
about the location of the VST plug-in folder containing the devices you want to use. In order to set up
your VST sources, press the Activate button in the browser’s Plug-Ins panel, or open the Plug-Ins
Settings by pressing Ctrl
section.

, (Mac). There you will find the Plug-In Sources

, (Win) / Cmd

Setting up VST Plug-In Sources for Windows.

For Windows, proceed as follows:

1.

2.

3.

Use the VST Plug-In Custom Folder entry to tell Live about the location of your VST plug-ins:
Click the Browse button to open a folder-search dialog for locating and selecting the
appropriate folder.
Once you have selected a VST Custom Folder and Live has scanned it, the path will be
displayed. Note that, on Windows, Live may have found a path in the registry without the need
for browsing.
Make sure that the Use VST Plug-In Custom Folder option is set to “On,“ so that your selected
folder is an active source for VST plug-ins in Live. Note that you can choose not to use your VST
plug-ins in Live by turning off the Use VST Plug-In Custom Folder option.

Setting up VST Plug-In Sources for macOS.

Set up your VST plug-ins under macOS by doing the following:

1.

2.

3.

Your VST plug-ins will normally be installed in the following folder in your home and local
directories: /Library/Audio/Plug-Ins/VST. You can turn Live’s use of these plug-ins on or off
with the Use VST plug-ins in System Folders option.
You may have an alternative folder in which you store your VST plug-ins (perhaps those that
you use only with Live). You can use VST plug-ins in this folder in addition to, or instead of,
those in the System folders. To tell Live about the location of this folder, click the Browse button
next to the VST Plug-In Custom Folder entry to open a folder-search dialog for locating and
selecting the appropriate folder.
Note that you can turn off your VST plug-ins in this folder using the Use VST Plug-In Custom
folder option.

Once you have configured your Plug-Ins Settings, the browser will display all plug-ins it finds in the
selected VST plug-in folder(s) as well as any sub-folders.

It is also possible to use VST plug-ins stored in different folders on your computer. To do this, create a
macOS or Windows alias of the folder where additional VST plug-ins are stored, and then place the
alias in the VST Plug-In Custom folder (or in the VST Plug-In System folder on macOS) selected in
Live’s Plug-Ins Settings. The alias can point to a different partition or hard drive on your computer. Live
will scan the set VST plug-in folder as well as any alias folders contained therein.

Some VST plug-ins contain errors or are incompatible with Live. During the scanning process, these
may cause the program to crash. When you re-launching Live, a dialog will appear to inform you
about which plug-in caused the problem. Depending on what Live detects about the plug-in, you may
be given the choice between performing another scan or making the problematic plug-in unavailable.
If you choose to rescan and they crash the program a second time, Live will automatically make them
unavailable, meaning that they will not appear in the browser and will not be rescanned again until
they are reinstalled.

21.3.2 VST Presets and Banks

Every VST plug-in instance “owns“ a bank of presets. A preset is meant to contain one complete set of
values for the plug-in’s controls.

To select a preset from the plug-in’s bank, use the chooser below the title bar. The number of presets
per bank is fixed. You are always working “in“ the currently selected preset, that is, all changes to the
plug-in’s controls become part of the selected preset.

The VST Plug-In Preset Chooser.

Note that VST presets are different from Live device presets: Whereas the presets for a Live device are
shared amongst all instances and Live Sets, the VST presets “belong“ to this specific instance of the
VST plug-in.

To rename the current preset, select the VST’s Device Title Bar and execute the Edit menu’s Rename
Plug-In Preset command. Then type in a new preset name and confirm by pressing Enter .

Renaming a VST Plug-In Preset.

VST presets and banks can be imported from files. Clicking a VST’s Load Preset or Bank button brings
up a standard file-open dialog for locating the desired file.

The VST Load Preset or Bank Button (Left) and Save Preset or Bank Button (Right).

Windows only: Please select from the File Type filter in the Windows dialog whether you want to
locate VST Presets (VST Program Files) or VST Banks (VST Bank Files).

To save the currently selected preset as a file, click the VST Save Preset or Bank button to bring up a
standard file-save dialog; select “VST Preset“ from the Format menu (Mac)/from the File Type menu
(Windows); select a folder and name. For saving the entire bank as a file, proceed likewise but
choose “VST Bank“ as a file type/format.

21.4 Audio Units Plug-Ins

Audio Units plug-ins are only available in macOS. In most respects, they operate just like VST plug-
ins.

An Audio Units Plug-In.

The first time you open Live, Audio Units plug-ins will not appear in the browser. In order to activate
your Audio Units as a plug-in source, please press the Activate button in the browser’s Plug-Ins label,
or go to the Plug-Ins Settings by pressing Ctrl
, (Mac). There you will find the
Plug-In Sources section. Turning on the Use Audio Units option activates Audio Units plug-ins so that
they appear in Live’s browser.

, (Win) / Cmd

Note that you can always turn this option off later if you decide not to use Audio Units.

Activating Audio Units Plug-Ins.

Audio Units plug-ins sometimes have a feature that allows choosing between different modes for the
device. You might be able to choose, for example, between different levels of quality in the rendering
of a reverb. Choosers for these device modes can only be accessed through the original plug-in
panel, which is opened using the Show/Hide Plug-In Window button.

Opening an Audio Units Plug-In Window.

Audio Units have presets that function just like those for the Live effects. However, some AU presets
cannot be dragged to different locations in the browser, as they are read-only.

Audio Units presets have an .au preset extension and are stored in the following directory according
to their manufacturer’s name:

(Home)/Library/Audio/Presets/(Manufacturer Name)/(Plug-in Name)

21.5 Device Delay Compensation

Live automatically compensates for delays caused by Live and plug-in instruments and effects,
including those on the return tracks. These delays can arise from the time taken by devices to process
an input signal and output a result. The compensation algorithm keeps Live’s tracks in sync while
minimizing delay between the player’s actions and the audible result.

Device delay compensation is on by default and does not normally have to be adjusted in any way.
To manually turn latency compensation on (or off), use the Delay Compensation option in the Options
menu.

When Delay Compensation is on, the Reduced Latency When Monitoring option is available in the
Options menu. This option toggles latency compensation on and off for tracks which have input
monitoring on. When enabled, input-monitored tracks will have the lowest possible latency, but may
be out of sync with some other tracks in your Set, such as Return tracks, which are still delay
compensated. When disabled, all tracks will be in sync, but input-monitored tracks may have higher
latency.

Note that tempo-synced effects and other devices that get timing information from Live’s internal clock
may sound out of sync if they are placed in a device chain after devices which cause delay.

Unusually high individual track delays or reported latencies from plug-ins may cause noticeable
sluggishness in the software. If you are having latency-related difficulties while recording and playing
back instruments, you may want to try turning off device delay compensation, however this is not
normally recommended. You may also find that adjusting the individual track delays is useful in these
cases, but please note that the Track Delay controls are unavailable when device delay compensation
is deactivated.

Note that device delay compensation can, depending on the number of tracks and devices in use,
increase the CPU load.

22. Instrument, Drum and Effect Racks

Inside An Audio Effect Rack.

A Rack is a flexible tool for working with effects, plug-ins and instruments in a track’s device chain.
Racks can be used to build complex signal processors, dynamic performance instruments, stacked
synthesizers and more. Yet they also streamline your device chain by bringing together your most
essential controls. While Racks excel at handling multiple devices, they can extend the abilities of
even a single device by defining new control relationships between its parameters.

22.1 An Overview of Racks

22.1.1 Signal Flow and Parallel Device Chains

Inside An Audio Effect Rack.

In any of Live’s tracks, devices are connected serially in a device chain, passing their signals from one
device to the next, left to right. By default, the Device View displays only a single chain, but there is
actually no limit to the number of chains contained within a track.

Racks allow (among other things) additional device chains to be added to any track. When a track
has multiple chains, they operate in parallel: In Instrument and Effect Racks, each chain receives the
same input signal at the same time, but then processes its signal serially through its own devices. The
output of each of the parallel chains is mixed together, producing the Rack’s output.

Drum Racks also allow multiple parallel chains to be used simultaneously, but their chains process
input somewhat differently: Rather than receiving the same input signals, each Drum Rack chain
receives input from only a single assigned MIDI note.

The entire contents of any Rack can be thought of as a single device. This means that adding a new
Rack at any point in a device chain is no different than adding any other device, and Racks can
contain any number of other Racks. If more devices are placed after a Rack in a track’s device chain,
the Rack’s output is passed on to them, as usual.

22.1.2 Macro Controls

The Macro Controls.

One unique property of Racks are their Macro Controls.

The Macro Controls are a bank of knobs, each capable of addressing any number of parameters
from any devices in a Rack. How you use them is up to you — whether it be for convenience, by
making an important device parameter more accessible; for defining exotic, multi-parameter morphs
of rhythm and timbre; or for constructing a mega-synth, and hiding it away behind a single
customized interface. See Using the Macro Controls for a detailed explanation of how to do this.

For the greatest degree of expression, try MIDI-mapping the Macro Controls to an external control
surface.

22.2 Creating Racks

Four Rack variants cover the range of Live’s devices: Instrument Racks, Drum Racks, Audio Effect Racks
and MIDI Effect Racks. Just as with track types, each kind of Rack has rules regarding the devices it
contains:

•
•

•

•

MIDI Effect Racks contain only MIDI effects, and can only be placed in MIDI tracks.
Audio Effect Racks contain only audio effects, and can be placed in audio tracks. They can also
be placed in MIDI tracks, as long as they are “downstream“ from an instrument.
Instrument Racks contain instruments, but can additionally contain both MIDI and audio effects.
In this case, all MIDI effects have to be at the beginning of the Instrument Rack’s device chain,
followed by an instrument, and then any audio effects.
Drum Racks are similar to Instrument Racks; they can contain instruments as well as MIDI and
audio effects and their devices must be ordered according to the same signal flow rules. Drum
Racks can also contain up to six return chains of audio effects, with independent send levels for
each chain in the main Rack.

There are different ways to create Racks. A new, empty Rack can be created by dragging a generic
Rack preset (“Audio Effect Rack,“ for example) from the browser into a track. Devices can then be
dropped directly into the Rack’s Chain List or Devices view, which are introduced in the next section.

If a track already has one or more devices that you would like to group into a Rack, then simply select
the title bars of those devices in the Device View, and right-click on one of the title bars to reveal the
Group and Group to Drum Rack commands in the context menu. Note that if you repeat this
command again on the same device, you will create a Rack within a Rack. You can also group
multiple chains within a Rack using the same procedure. Doing this also creates a Rack within a Rack.
In the Device View, the contents of Racks are always contained between end brackets: Just as with
punctuation or in mathematics, a Rack within a Rack will have a pair of brackets within a pair of
brackets.

To ungroup devices, dismantling their Racks, select the Rack’s title bar, and then use the Edit menu or
the context menu to access the Ungroup command.

22.3 Looking at Racks

Components of an Effect Rack.

Components of a Drum Rack.

1.

2.
3.
4.
5.

6.

Racks have distinct views that can be shown or hidden as needed. Therefore, every Rack has a
view column on its far left side that holds the corresponding view selectors. The actual view
selectors available differ depending on whether an Instrument, Drum or Effect Rack is being
used.
Macro Controls
Chain List - In Drum Racks, this view can include both drum chains and return chains.
Devices
Racks are also identifiable by their round corners, which bracket and enclose their content.
When the Devices view is shown, the end bracket visually detaches itself to keep the Rack
hierarchy clear.
Pad View - This is unique to Drum Racks.

To move, copy or delete an entire Rack at once, simply select it by its title bar (as opposed to the title
bars of any devices that it contains). When selected, a Rack can also be renamed by using the Edit
menu’s Rename command. You can also enter your own info text for a Rack via the Edit Info Text
command in the Edit menu or in the Racks’s context menu.

When all of a Rack’s views are hidden, its title bar will fold into the view column, making the entire
Rack as slim as possible. This has the same effect as choosing Fold from the context menu or double-
clicking on the Rack’s title bar.

If you would like to locate a particular device in a Rack without searching manually through its entire
contents, you will appreciate this navigation shortcut: right-click on the Device View selector, and a
hierarchical list of all devices in the track’s device chain will appear. Simply select an entry from the
list, and Live will select that device and move it into view for you.

Navigate Racks Quickly Via a Context Menu.

22.4 Chain List

The Chain List in an Audio Effect Rack.

As signals enter a Rack, they are first greeted by the Chain List. We will therefore also choose this
point for our own introduction.

The Chain List represents the branching point for incoming signals: Each parallel device chain starts
here, as an entry in the list. Below the list is a drop area, where new chains can be added by
dragging and dropping presets, devices, or even pre-existing chains.

Note: Racks, chains and devices can be freely dragged into and out of other Racks, and even
between tracks. Selecting a chain, then dragging and hovering over another Session or Arrangement
View track will give that track focus; its Device View will open, allowing you to drop your chain into
place.

Since the Device View can show only one device chain at a time, the Chain List also serves as a
navigational aid: The list selection determines what will be shown in the adjacent Devices view (when
enabled). Try using your computer keyboard’s up and down arrow keys to change the selection in the
Chain List, and you’ll find that you can quickly flip through the contents of a Rack.

The Chain List also supports multi-selection of chains, for convenient copying, organizing and
regrouping. In this case, the Devices view will indicate how many chains are currently selected.

Each chain has its own Chain Activator, as well as Solo and Hot-Swap buttons. Chains in Instrument,
Drum and Audio Effect Racks also have their own volume and pan sliders, and Drum Rack chains
have additional send level and MIDI assignment controls. Like Live Clips, entire chains can be saved
and recalled as presets in the browser. You can give a chain a descriptive name by selecting it, then
choosing the Edit menu’s Rename command. You can also enter your own info text for a chain via the
Edit Info Text command in the Edit menu or in the chain’s context menu. The context menu also contains
a color palette where you can choose a custom chain color.

22.4.1 Auto Select

Auto Select in an Audio Effect Rack.

When the Auto Select switch is activated, every chain that is currently processing signals becomes
selected in the Chain List. In Drum Racks, this feature will select a chain if it receives its assigned MIDI

input note. In Instrument and Effect Racks, Auto Select works in conjunction with zones, which are
discussed next, and is quite helpful when troubleshooting complex configurations.

22.5 Zones

Zones are sets of data filters that reside at the input of every chain in an Instrument or Effect Rack.
Together, they determine the range of values that can pass through to the device chain. By default,
zones behave transparently, never requiring your attention. They can be reconfigured, however, to
form sophisticated control setups. The three types of zones, whose editors are toggled with the buttons
above the Chain List, are Key, Velocity, and Chain Select. The adjacent Hide button whisks them out
of sight.

Note: Audio Effect Racks do not have key or velocity zones, since these two zone types filter MIDI
data only. Likewise, Drum Racks have no zones at all; they filter MIDI notes based on choosers in their
chain lists.

Zones contain a lower, main section, used for resizing and moving the zone itself, and a narrow
upper section that defines fade ranges. Resizing of either section is done by clicking and dragging on
its right or left edges, while moving is accomplished by clicking and dragging a zone from anywhere
except its edges.

22.5.1 Signal Flow through Zones

To understand how zones work, let’s examine the signal flow in a MIDI Effect Rack. Our MIDI Effect
Rack resides in the device chain of a MIDI track, and therefore processes MIDI signals. We will
assume that it contains four parallel device chains, each containing one MIDI effect.

1.

2.

3.

4.

5.

6.

All MIDI data in the track is passed to its device chain, and therefore into the input of the MIDI
Effect Rack.
Our MIDI Effect Rack has four device chains, all of which receive the same MIDI data at the
same time.
Before any MIDI data can enter a device chain, it must be able to pass through every zone in
that chain. Every chain in a MIDI Effect Rack has three zones: a key zone, a velocity zone and
a chain select zone.
An incoming MIDI note gets compared to a chain’s key zone. If the MIDI note lies within the
key zone, it is passed to the next zone for comparison; if it does not, then we already know that
the note will not be passed to that chain’s devices.
The same comparisons are made for the chain’s velocity and chain select zones. If a note also
lies within both of these zones, then it is passed to the input of the first device in that chain.
The output of all parallel chains is mixed together to produce the MIDI Effect Rack’s final output.
If there happened to be another device following after the Rack in the track’s device chain, it
would now receive the Rack’s output for processing.

22.5.2 Key Zones

The Key Zone Editor.

When the Key button is selected, the Key Zone Editor appears to the right of the Chain List, illustrating
how each chain maps to the full MIDI note range (nearly 11 octaves). Chains will only respond to
MIDI notes that lie within their key zone. The zones of individual chains may occupy any number of
keys, allowing for flexible “keyboard split“ setups.

Key zone fade ranges attenuate the velocities of notes entering a chain.

22.5.3 Velocity Zones

The Velocity Zone Editor.

Each chain in an Instrument Rack or MIDI Effect Rack also has a velocity zone, specifying the range of
MIDI Note On velocities that it will respond to.

The Velocity Zone Editor, when displayed, replaces the Key Zone Editor to the right of the Chain List.
MIDI Note On velocity is measured on a scale of 1-127, and this value range spans the top of the
editor. Otherwise, the functionality here is identical to that of the Key Zone Editor.

Velocity zone fade ranges attenuate the velocities of notes entering a chain.

22.5.4 Chain Select Zones

The Chain Select Editor.

Activating the Chain button in an Instrument or Effect Rack displays the Chain Select Editor. These
Racks have chain select zones, which allow you to filter chains spontaneously via a single parameter.
The editor has a scale of 0-127, similar to the Velocity Zone Editor. Above the value scale, however,
you will find a draggable indicator known as the Chain selector.

The chain select zone is a data filter just like the other zones; although all chains in a Rack receive
input signals, only those with chain select zones that overlap the current value of the Chain selector
can be addressed and thereby produce output.

By default, the chain select zones of Instrument and MIDI Effect Racks filter only notes, ignoring all
other incoming MIDI events (such as MIDI CCs). To filter all MIDI events, enable the Chain Selector
Filters MIDI Ctrl option, available in the context menu of a Rack’s Chain Select Ruler.

In MIDI Effect Racks, fade ranges attenuate the velocities of notes entering a chain. In Instrument
Racks and Audio Effect Racks, which both output audio signals, fade ranges attenuate the volume
level at each chain’s output. So what happens, then, if the Chain selector is moved outside of the chain
select zone where a sound is currently playing? If the zone ends in a fade range, the chain’s output
volume is attenuated to zero while the Chain selector is outside of the zone. If the zone had no fade
range, the output volume is not attenuated, allowing the chain’s effects (like long reverb tails or
delays) to fade out according to their own settings.

Let’s consider how we can make use of chain select zones in a performance situation:

22.5.4.1 Making Preset Banks Using Chain Select

Using Chain Select Zones to Create Effects Presets.

Unlike the other zone types, the default length of a chain select zone is 1, and the default value is 0.
From this setup, we can quickly create “preset banks“ using the Chain Select Editor.

Again, we will use a Rack with four chains as our starting point. Each of the four chains contain
different effects that we would like to be able to switch between. To make this a “hands-on“
experience, we have MIDI-mapped the Chain selector to an encoder on an external control surface.

Let’s move the chain select zones of the second and third chains so that each of our zones is
occupying its own adjacent value: The first chain’s zone has a value of 0, the second chain’s zone has
a value of 1, the third has a value of 2, and the fourth has a value of 3.

Since each of our chain select zones has a unique value, with no two zones overlapping, we now
have a situation where only one chain at a time can ever be equal to the Chain selector value (shown
at the top of the editor). Therefore, by moving the Chain selector, we determine which chain can
process signals. With our MIDI encoder at hand, we can now flip effortlessly between instrument or
effect setups.

22.5.4.2 Crossfading Preset Banks Using Fade Ranges

Crossfading Between Effects Presets Using Chain Select Zones.

Taking the previous example one step further, we can tweak our chain select zones to produce a
smooth transition between our “presets.“ To accomplish this, we will make use of our zones’ fade
ranges.

To create some room for fading, let’s extend the length of our zones a bit. Setting the zones as shown
maintains four exclusive values for our presets, so that each still has one point where neither of the
others are heard. We crossfade between the presets over eight steps. If this is too rough a transition for
your material, simply reposition the zones to maximize the fade ranges.

22.6 Drum Racks

We’ve already talked a bit about Drum Racks, and most of their features are the same as those found
in Instrument and Effect Racks. But Drum Racks have a slightly different layout, some unique controls
and special behavior that is optimized for creating drum kits.

The Chain List in a Drum Rack.

1.

2.

3.

In addition to the standard selectors found on all Racks, Drum Racks have four additional
controls in the view column. From top to bottom, these are toggles for the Input/Output, Send,
and Return sections, and the Auto Select button.
Input/Output Section - The Receive chooser sets the incoming MIDI note to which the drum
chain will respond. The list shows note names, MIDI note numbers and standard GM drum
equivalents. The Play slider sets the outgoing MIDI note that will be sent to the devices in the
chain. The Choke chooser allows you to set a chain to one of sixteen choke groups. Any chains
that are in the same choke group will silence the others when triggered. This is useful for choking
open hihats by triggering closed ones, for example. If “All Notes“ is selected in the Receive
chooser, the Play and Choke choosers are disabled — in this case, the chain simply passes the
note that it receives to its devices. The small Preview button to the left of these choosers fires a
note into the chain, making it easy to check your mappings away from a MIDI controller.
Mixer Section - In addition to the mixer and Hot-Swap controls found in other Rack types,
Drum Racks also have send sliders. These sliders allow you to set the amount of post-fader
signal sent from each drum chain to any of the available return chains. Note that send controls
are not available until return chains have been created.

4.

Return Chains - A Drum Rack’s return chains appear in a separate section at the bottom of the
chain list. Up to six chains of audio effects can be added here, which are fed by send sliders in
each of the drum chains above.

The Audio To chooser in the mixer for return chains allows you to route a return chain’s output to either
the main output of the Rack or directly to the return tracks of the Set.

22.6.1 Pad View

Pad View.

The Pad View is unique to Drum Racks and offers an easy way to map and manipulate samples and
devices. Each pad represents one of the 128 available MIDI notes. The pad overview to the left shifts
the set of visible pads up or down in groups of 16, either by dragging the view selector to a new area
or by using your computer keyboard’s up and down arrow keys. Use the Alt (Win) / Cmd (Mac)
modifier to shift the view by single rows instead.

Almost any object from Live’s browser — samples, effects, instruments and presets — can be dragged
onto a pad, mapping automatically to the pad’s note and creating or reconfiguring internal chains
and devices as necessary. Dropping a sample onto an empty pad, for example, creates a new chain
containing a Simpler, with the dropped sample ready to play from the pad’s note. If you then drag an
audio effect to the same pad, it is placed downstream from the Simpler in the same chain. To replace

the Simpler, simply drop another sample onto the same pad — any downstream audio effects or
upstream MIDI effects will be left intact and only the Simpler and sample will be replaced.

In addition to dragging objects from the browser, pads can also be filled quickly via Hot-Swap. If
you’re in Hot-Swap mode, pressing the D key will toggle the Hot-Swap target between the Drum
Rack itself and the last selected pad.

If a multi-selection of samples is dropped onto a pad, new Simplers and chains will be mapped
upwards chromatically from this pad, replacing any other samples that may have already been
assigned to the pads in question (but, as before, leaving any effects devices alone). Alt (Win) /
Cmd (Mac)-dragging a multi-selection layers all of the samples to a single pad, by creating a nested
Instrument Rack.

Dragging a pad to another pad swaps the note mapping between the pads. This means that any
MIDI clips triggering the affected notes will now play the “wrong“ sounds — although this might be
exactly what you want. Alt (Win) / Cmd (Mac)-dragging one pad to another will layer any
chains from both pads in a nested Instrument Rack.

You can always change your mappings from within the chain list as well, by adjusting the Receive
choosers. The Pad View will update automatically to reflect your changes. If you set the same Receive
note for multiple chains, that note’s pad will trigger them all.

If you’re working with lots of nested Racks, the inner structure can quickly become complicated. Pad
View can make it much easier to work by letting you focus on only the top level: the notes and sounds.
It’s important to remember that a pad represents a note, rather than a chain. More specifically, it
represents all chains, no matter how deep in the Rack, that are able to receive that pad’s note. What
you can control with each pad is related to how many chains it represents:

•

•

•

An empty pad shows only the note it will trigger. When you mouse over it, the Status Bar will
display this note, as well as the suggested GM instrument.
A pad that triggers only one chain shows the name of the chain. In this case, the pad serves as
a handy front-end for many controls that are normally accessed in the chain list, such as mute,
solo, preview and Hot-Swap. You can also rename and delete the chain via the pad.
A pad that triggers multiple chains shows “Multi“ as its name, and its mute, solo and preview
buttons will affect all of its chains. If you mute and solo chains individually within the chain list,
the pad’s icons reflect this mixed state. Hot-Swap and renaming are disabled for a Multi pad,
but you can delete all of its chains at once.

Although Pad View is designed for easy editing and sound design, it also excels as a performance
interface, particularly when triggered by a hardware control surface with pads. If your pad controller
is one of Live’s natively supported control surfaces, simply select it as a control surface in the Link,
Tempo & MIDI tab of Live’s Settings. From then on, as long as you have a Drum Rack on a track that’s
receiving MIDI, your pad controller will trigger the pads that are visible on your screen. If you scroll
the pad overview to show a different set of pads, your controller will update automatically.

22.7 Using the Macro Controls

It is possible to use up to 16 Macro Controls in a Rack. When creating a new Rack, eight Macro
Control knobs are shown by default. You can use the
decrease the number of visible Macro Controls. Note that the state of shown and hidden Macro
Controls is saved in the Live Set.

 view selector buttons to increase or

 and

These Selector Buttons Set the Number of Visible Macro Controls.

22.7.1 Map Mode

Making Macro Control Assignments in Map Mode.

With the potential for developing complex device chains, Macro Controls keep things manageable
by taking over the most essential parameters of a Rack (as determined by you, of course). Once you
have set up your ideal mapping, the rest of the Rack can be hidden away.

The Macro Control view’s dedicated Map button opens the door to this behavior. Enabling Macro
Map Mode causes three things to happen:

•
•
•

All mappable parameters from a Rack’s devices will appear with a colored overlay;
Map buttons will appear beneath each Macro Control dial;
The Mapping Browser (see ‘The Mapping Browser’) will open.

The following steps will get you started mapping:

1.
2.
3.

4.

5.

Enable Macro Map Mode by clicking the Map mode button;
Select a device parameter for mapping by clicking it once;
Map the parameter by clicking on any Macro Control’s Map button. The details will be added
to the Mapping Browser. By default, the Macro Control will take its name and units from the
device parameter it is controlling.
Refine the value range if desired using the Min/Max sliders in the Mapping Browser. Inverted
mappings can be created by setting the Min slider’s value greater than the Max slider’s value.
The current values can also be inverted by right-clicking on the entry in the Mapping Browser
and selecting Invert Range.
Select another device parameter if you’d like to create more mappings, or click on the Map
mode button once more to exit Macro Map Mode.

Note that once assigned to a Macro Control, a device parameter will appear disabled, since it hands
over all control to the Macro Control (although it can still be modulated externally, via clip envelopes.

You can edit or delete your assignments at any time using the Mapping Browser (which only appears
when Map Mode is enabled).

If more than one parameter is assigned to a single Macro Control, the name of the control will revert
to its generic name (e.g., Macro 3). The Marco Control’s units will also change to a 0 to 127 scale,
except when all parameters possess both the same unit type and the same unit range.

Macro Controls can be given custom names, colors and info text entries via the corresponding
commands in the Edit menu or the context menu.

22.7.2 Randomizing Macro Controls

If you want to add an element of surprise or find some inspiration in your Set, randomizing Macro
Controls can be a useful tool. You can randomize the values of all mapped Macro Controls in a Rack
by pressing the Rand button in that Rack’s title bar.

This Button Randomizes Macro Controls.

Depending on your material, you might only want to randomize some parameters, while leaving other
controls unchanged. To exclude a mapped Macro Control from randomization, enable the Exclude
Macro from Randomization option in the context menu. Note that Macro Controls assigned to Volume
parameters in Instrument Rack presets are excluded from randomization by default.

22.7.3 Macro Control Variations

Macro Control Variations.

You can store different states of Macro Controls as individual presets (or “variations”). This is useful
when, for example, you want to capture the state of a Rack as a “snapshot” during a sound design
session, or audition different settings of a mapped Macro Control in an Audio Effect Rack made for
mixing. You can also use these variations or create builds and drops, or make instant jumps between
different Macro Control settings while recording or performing.

Clicking the Show/Hide Macro Variations view selector button opens a view where you can store,
manage and launch Macro Control variations.

This Selector Button Opens the Macro Control Variations View.

Pressing the New button stores the current state of a Rack’s Macro Controls as a new variation. By
default, each stored variation will be named sequentially as “Variation 1”, “Variation 2”, etc.
Selected Macro Control variations can be renamed, duplicated, or deleted via commands in the Edit
menu or the context menu.

A Macro Control variation can be launched in its stored state via the Launch Macro Variation button
to the right, or overwritten via the “Overwrite Macro Variation” button to the left. Note that you can
exclude a Macro Control from changing when a different Macro Control variation is launched, by
using the Exclude Macro From Variations command in the context menu. Disabling the context menu
entry will re-enable changes to that control.

22.8 Mixing With Racks

Any Instrument or Drum Rack that contains more than one chain can be viewed and mixed alongside
the tracks in the Session View’s mixer. A track that contains these Racks will have a
 button in its title
bar, which will fold the Rack’s mixer in or out. Likewise, any nested chains within the Rack will also
have this button. This makes it easy to get an overview of your Rack’s hierarchy — or hide it when you
just want to work on your mix.

Mixing Rack Chains in the Session View.

Chains in the Session View mixer look similar to tracks, but they have no clip slots. Their mixing and
routing controls mirror those found in the Rack’s chain list, so any changes made to these controls in
either area will be reflected in the other immediately. Likewise, many chain operations such as
reordering, renaming and regrouping can be performed from either the mixer or the chain list.
Clicking in a chain’s mixer title bar shows only that chain’s devices in the Device View.

As with tracks, when chains are multiselected in the Session View mixer, adjusting a mixer parameter
for one of the chains will adjust the same parameter in the other selected chains. Note that this
behavior only applies to parameters adjusted via the Session mixer and not when adjusting the same
parameters in the Rack’s chain list.

22.8.1 Extracting Chains

All chains can be dragged from their parent Racks and placed into other tracks or Racks, either from
the chain list or from the Session View mixer. A Drum Rack’s return chains can also be extracted, and
will create new return tracks if dragged to the mixer. Drum chains have an additional feature: when
dragged from the mixer to a new track, they take their MIDI notes with them. For example, if you are
working on a MIDI drum loop within a single track and decide that you would like to move just the
snare onto its own track, simply select the snare chain’s title bar in the mixer and drag it to the mixer’s
drop area. This creates a new track with the full contents of the snare chain: both its devices and its
MIDI data. If you would like to extract only the devices, drag from the chain list instead of from the
mixer.

Extracting Drum Chains in the Mixer Extracts MIDI Data.

23. Automation and Editing Envelopes

Often, when working with Live’s mixer and devices, you will want the controls’ movements to become
part of the music. The movement of a control across the song timeline or Session clip is called
automation; a control whose value changes in the course of this timeline is automated. Practically all
mixer and device controls in Live can be automated, including the song tempo.

23.1 Recording Automation in Arrangement View

Automation can be recorded to the Arrangement View in two ways:

1.
2.

By manually changing parameters while recording new material directly into the Arrangement.
By recording a Session View performance into the Arrangement, if the Session clips contain
automation.

During Session-to-Arrangement recording, automation in Session clips is always recorded to the
Arrangement, as are any manual changes to parameters in tracks that are being recorded from the
Session.

When recording new material directly to the Arrangement, the Automation Arm button determines
whether or not manual parameter changes will be recorded.

The Automation Arm Button.

When Automation Arm is on, all changes of a control that occur while the Control Bar’s Arrangement
Record button is on become Arrangement automation. Try recording automation for a control; for
instance a mixer volume slider. After recording, play back what you have just recorded to see and
hear the effect of the control movement. You will notice that a little LED has appeared in the slider
thumb to indicate that the control is now automated. Try recording automation for track panning and
the Track Activator switch as well; their automation LEDs appear in their upper left corners.

Volume, Pan and the Track Activator Switch Have Been Automated.

23.2 Recording Automation in Session View

Automation can also be recorded to Session View clips. Here is how it works:

Controls for Recording Session Automation.

1.
2.

3.

Enable the Automation Arm button to prepare for automation recording.
Activate the Arm button for the tracks onto which you want to record. Clip Record buttons will
appear in the empty slots of the armed tracks.
Click the Session Record button to begin recording automation.

It is also possible to record automation into all playing Session clips, regardless of whether or not they
are in armed tracks. This is done via the Session Automation Recording switch in the Record, Warp &
Launch Settings.

The Session Automation Recording Preference.

This allows you to, for example, overdub Session automation into an existing MIDI clip without also
recording notes into the clip.

Any automation in Session View becomes track-based automation when clips are recorded or copied
into Arrangement View.

23.2.1 Session Automation Recording Modes

The automation recording behavior differs depending on how you adjust parameters while recording.
When using the mouse, recording stops immediately when you let go of the mouse button. This is
referred to in some editing applications as “touch” behavior. When adjusting parameters via knobs or
faders on MIDI controllers, recording will continue as long as you adjust the controller. When you let
go, recording will continue until the end of the clip’s loop and then will “punch out” automatically. This
is known as “latch” behavior in some applications.

23.3 Deleting Automation

To delete all automation data, right-click on an automated control to open its context menu and select
Delete (Mac) shortcut keys. The
Delete Automation, or press the Ctrl
automation LED disappears, and the control’s value stays constant across the entire Arrangement
timeline and in any Session View clips. You can also delete selected portions of automation by editing
breakpoint envelopes.

Backspace (Win) / Cmd

23.4 Overriding Automation

In practice, you will often want to try out new control moves without overwriting existing automation
data in the Arrangement. Well, nothing is forever in the world of infinite Undo, but it’s easy to disable
a control’s automation temporarily to avoid overwriting existing data: If you change an automated
control’s value while not recording, the automation LED goes off to indicate the control’s automation is
inactive. Any automation is therefore overridden by the current manual setting.

When one or more of the automated controls in your Live Set are not active, the Control Bar’s Re-
Enable Automation button lights up.

The Re-Enable Automation Button.

This button serves two purposes. It reminds you that the current state of the controls differs from the
state captured in Session clips or the Arrangement, and you can click on it to reactivate all automation
and thereby return to the automation state as it is written “on tape.“

You can also re-enable automation for only one parameter via the Re-Enable Automation option in
the context menu for that parameter. And in the Session View, you can re-enable overridden
automation by simply relaunching a clip that contains automation.

23.5 Drawing and Editing Automation

In the Arrangement View and in Session View clips, automation can be viewed and edited as
breakpoint envelopes.

Here is how automation editing works in the Arrangement:

Automation Envelopes in the Arrangement View.

1.

2.

3.

4.

 toggle button

 toggle button or A shortcut key again.

To show automation envelopes, enable Automation Mode by clicking the
above the track headers, or using the A shortcut to the View menu item. Note that you can
disable Automation Mode by pressing the
Clicking on a track’s mixer or device controls will display this control’s envelope on the clip
track.
Envelopes appear in the track’s main automation lane, “on top of“ the audio waveform or MIDI
display. This is useful for lining up breakpoints with the track’s audio or MIDI content. An
envelope’s vertical axis represents the control value and the horizontal axis represents time. For
switches and radio buttons, the value axis is “discrete”, meaning that it operates with non-
continuous values (e.g., on/off).
The Device chooser either selects the track mixer, one of the track’s devices, or “None“ to hide
the envelope. It also provides you with an overview of which devices actually have automation

by showing an LED next to their labels. You can make things clearer still by selecting “Show
Automated Parameters Only“ from the bottom of the chooser.
The Automation Control chooser selects a control from the device chosen in the Device chooser.
The labels of automated controls have an LED.

5.

Once an envelope has been selected on the track, several new buttons appear:

1.

2.

3.

 button moves the envelope into its own automation lane below the clip. You can then

The
select another automation parameter from the choosers to view it simultaneously. Holding Alt
(Win) / Cmd (Mac) while pressing the
 button moves the selected envelope, as well as all
automated envelopes, into their own automation lane(s) below the clip. If the Device chooser is
set to “None“, this button will be hidden.
The
deactivate its envelope. Holding Alt (Win) / Cmd (Mac) while clicking the
 button
removes the selected automation lane, as well as any subsequent automation lanes in that
track.
The
lets you show or hide all additional automation lanes.

 button hides its respective automation lane. Note that hiding a lane from view does not

 toggle appears when an envelope is moved into its own automation lane. This toggle

Right-clicking on an automation lane header opens a context menu with additional options for
viewing envelopes. This context menu also contains commands to quickly clear all automation
envelopes for the track or any of its devices.

You can use the left arrow key to navigate from an automation lane to the main track, this will fold all
automation lanes as well. Using the left and right arrow keys on a main track will fold/unfold its
automation lanes.

Automation editing for Session View clips is covered in detail in the Clip Envelopes chapter.

23.5.1 Drawing Envelopes

With Draw Mode enabled, you can click and drag to “draw“ an envelope curve.

The Draw Mode Switch.

To toggle Draw Mode, select the Draw Mode option from the Options menu, click on the Control
Bar’s Draw Mode switch, or press B . Holding B while editing with the mouse temporarily toggles
Draw Mode.

Drawing an Envelope.

Drawing creates steps as wide as the visible grid, which you can modify using a number of handy
shortcuts. Holding down the Shift modifier while dragging vertically allows you to adjust the
automation value of a step at a finer resolution.

For freehand drawing, you can hide the grid using the Snap to Grid Options menu entry or the Ctrl
4 (Win) / Cmd
shown, hold down Alt (Win) / Cmd (Mac) while drawing.

4 (Mac) shortcut. To temporarily enable freehand drawing while the grid is

23.5.2 Editing Breakpoints

With Draw Mode off, the envelope display looks and works differently. The line segments and the
breakpoints connecting them become draggable objects. Clicking and dragging in the envelope’s
background defines a selection. Here’s how editing breakpoints works:

•
•

•
•

Click at a position on a line segment to create a new breakpoint there.
Double-click anywhere in the envelope display that is not on a line segment, to create a new
breakpoint there.
Click on a breakpoint to delete it.
To help you edit breakpoints more quickly, automation values are shown when you create,
hover over, or drag a breakpoint. Note that when hovering over or dragging a selected line
segment, the automation value shown will correspond to the breakpoint closest to the cursor.

A Breakpoint’s Automation Value.

•

•

•

Click and drag a breakpoint to move it to the desired location. If the breakpoint you are
dragging is in the current selection, all other breakpoints in the selection will follow the
movement. When dragging a breakpoint, a thin black vertical line will appear to help you see
where your breakpoint is positioned in relation to the grid lines.
Right-click on a breakpoint and choose Edit Value from the context menu. This allows you to set
an exact value in the editable field using your computer keyboard. If multiple breakpoints are
selected, they will all be moved relatively. Similarly, you can also create new breakpoints at an
exact value by right-clicking on a preview breakpoint and choosing the Add Value command.
Click near (but not on) a line segment or hold Shift and click directly on a line segment to
select it. With the left mouse button held down, drag to move the line segment to the desired
location. If the line segment you are dragging is in the current time selection, Live will insert
breakpoints at the selection’s edges and the entire segment will move together.

To Move all Breakpoints Within the Selection, Drag Any One of Them.

•

•

•

Breakpoints created close to a grid line will automatically snap to that line. Hold down the
Alt (Win) / Cmd (Mac) modifier while dragging horizontally to bypass grid snapping.
Breakpoints and line segments will snap to time positions where neighboring breakpoints exist.
You can remove a neighboring breakpoint by continuing to drag a breakpoint or line segment
“over” it horizontally.
When moving a line segment or breakpoint, hold Shift while dragging to restrict movement
to either the horizontal or vertical axis.

•

•

Holding down the Shift modifier while dragging vertically allows you to adjust the
breakpoint or line segment value at a finer resolution.
Hold Alt (Win) / Option (Mac) and drag a line segment to curve the segment. Double-
click while holding Alt (Win) / Option (Mac) to return the segment to a straight line.

A Curved Envelope Segment.

23.5.3 Stretching and Skewing Envelopes

The Handles Allow You to Stretch or Skew Envelopes.

When hovering over a time selection, handles appear around the outer edges of the selection.
Clicking and dragging these handles allows you to transform the selected automation in the following
ways:

•

Dragging the top and bottom center handles lets you stretch the automation along the vertical
axis. While dragging, a rectangle indicates the amount of stretching. The rectangle will snap to
upper and lower boundaries and when its corners intersect. Holding Shift allows you to
finely adjust the amount of stretching. Dragging beyond the boundaries will clip the envelope.

While Dragging a Handle, A Rectangle Indicates the Amount of Stretching or Skewing.

•

•

•

Dragging the left and right center handles lets you stretch the automation along the horizontal
axis. Dragging over existing breakpoints outside the time selection will remove them. If you hold
Shift while stretching, these breakpoints will be moved in proportion to the movement of the
handle. Hold down the Alt (Win) / Cmd (Mac) modifier while dragging horizontally to
bypass grid snapping.
Dragging any of the corner handles lets you skew the automation. While dragging, a rectangle
indicates the degree of skewing. The rectangle will snap to upper and lower boundaries and
when its corners intersect. Holding Shift allows you to finely adjust the amount of skewing.
Dragging a handle while holding Alt (Win) / Option (Mac) will mirror the movement in
the opposite handle, as if you were dragging them both simultaneously in opposite directions.

23.5.4 Simplifying Envelopes

If your automation envelope has a lot of breakpoints, e.g., after recording automation, the Simplify
Envelope command can be quite useful. Simplify Envelope calculates the optimal number of
breakpoints needed to represent the selected automation envelope, and removes any unnecessary
breakpoints, replacing them with straight lines or curved segments where appropriate.

The Simplify Envelope Command Removes Unnecessary Breakpoints.

Make a time selection on the automation you wish to simplify, and choose Simplify Envelope from the
context menu.

23.5.5 Inserting Automation Shapes

Automation Shapes Inserted into an Envelope.

Automation shapes can help you quickly create complex rhythmic automation patterns, as well as
more subtle, slow-paced movements like swells, builds and drops.

There are several predefined automation shapes that you can apply to a time selection. To insert an
automation shape, right-click on a time selection and choose a shape from the context menu.

The Two Rows Contain Different Types of Automation Shapes.

There are two types of automation shapes. In the top row of available shapes, you’ll find several
common waveforms: sine, triangle, sawtooth, inverse sawtooth and square. When inserted, these
shapes will be scaled horizontally to the time selection and vertically to the automated parameter
range. If there is no time selection, the shapes will be scaled horizontally to the current grid size.

In the bottom row of available shapes are two sets of ramps, and an ADSR shape. These shapes
behave slightly differently than those on the top row. When inserted, they will link up to the value of
the automation before or after the selection, as indicated by their dotted line.

23.5.6 Locking Envelopes

When moving Arrangement View clips, Live normally moves all automation with the clip. Sometimes,
you might want to lock the envelopes to the song position rather than to the clips, and the Lock
Envelopes switch does just that.

You can also choose to lock envelopes from the Options menu.

The Lock Envelopes Switch.

23.5.7 Edit Menu Commands

When working with automation data in the Arrangement View, several Edit menu commands behave
differently depending on whether or not your selection is within the clip track or its automation lanes.

Cut, Copy, Duplicate or Delete commands applied to an envelope selection within a single lane will
only apply to this envelope. The clip itself and other automation that occurs in that time selection will
be unaffected. You can also work with envelopes in multiple lanes simultaneously.

If you want your edits to apply to both the clip and all of its associated envelopes, ensure the Lock
Envelopes switch is disabled and apply edit commands to a selection in the clip track.

Note that Live allows you to copy and paste envelope movements not only from one point in time to
another, but also from one parameter to another. Since the parameters may be completely unrelated,
this can have unexpected (but possibly interesting) results.

23.5.8 Editing the Tempo Automation

The ability to dynamically stretch and compress audio to track any tempo or tempo variation is one of
Live’s specialties. In Live, the song tempo is just another automated control.

To edit the song tempo envelope, unfold the Main track in Arrangement View, choose “Mixer“ from
the top envelope chooser and “Song Tempo“ from the bottom one.

The Tempo Envelope.

When adjusting the tempo envelope, you might want to scale the value axis display, which is the
function of the two value boxes below the envelope choosers: The left box sets the minimum, and the
right box sets the maximum tempo displayed, in BPM.

Note that these two controls also determine the value range of a MIDI controller assigned to the
tempo.

24. Clip Envelopes

Every clip in Live can have its own clip envelopes. The aspects of a clip that are influenced by clip
envelopes change depending upon clip type and setup; clip envelopes can do anything from
representing MIDI controller data to automating or modulating device parameters. In this chapter, we
will first look at how all clip envelopes are drawn and edited, and then get into the details of their
various applications.

24.1 The Clip Envelope Editor

To work with clip envelopes, open up the Clip View’s Envelopes tab by clicking the tab header with
 icon in the Clip View. The Envelopes tab contains two choosers for selecting an envelope to
the
view and edit.

The Clip View’s Envelopes Tab.

The left-hand side menu is the Device chooser, which selects a general category of controls with
which to work. Device chooser entries are different for different kinds of clips:

•

•

Audio clips have entries for “Clip” (the clip’s sample controls), every effect in the track’s device
chain, and the mixer.
MIDI clips have entries for “MIDI Ctrl“ (MIDI controller data), every device in the track’s device
chain, and the mixer.

The right-hand side menu, the Control chooser, selects among the controls of the item chosen in the
Device chooser menu. In both choosers, parameters with altered clip envelopes appear with LEDs

next to their names. You can simplify the appearance of these choosers by selecting “Only show
adjusted envelopes” from either of them.

The techniques for drawing and editing clip envelopes are the same as those for automation
envelopes in the Arrangement View. Please see Recording Automation in Session View for information
on recording Session View automation.

To delete a clip envelope (i.e., to set it back to its default value), right-click in the Clip View’s Envelope
Editor or press the Ctrl
context menu and select Clear Envelope.

Delete (Mac) shortcut keys to open its

Backspace (Win) / Cmd

To automatically reset certain MIDI control messages at the start of a new clip, select the “MIDI
Envelope Auto-Reset” entry from the Options menu or the context menu in the Sample Editor.

Let us now look at some uses of clip envelopes.

24.2 Audio Clip Envelopes

Clip envelopes extend Live’s “elastic“ approach to audio and, in conjunction with Live’s audio effects,
turn Live into a mighty sound-design tool. Using clip envelopes with audio clips, you can create an
abundance of interesting variations from the same clip in real time — anything from subtle corrections
to entirely new and unrelated sounds.

24.2.1 Clip Envelopes are Non-Destructive

Using clip envelopes, you can create new sounds from a sample without actually affecting the sample
on disk. Because Live calculates the envelope modulations in real time, you can have hundreds of
clips in a Live Set that all sound different, but use the same sample.

You can, of course, export a newly created sound by rendering, or by resampling. In the Arrangement
View, you can use the Consolidate command to create new samples.

24.2.2 Changing Pitch and Tuning per Note

Drop a sample loop from the browser into Live, make sure the Warp switch is enabled, and then play
the clip. Select “Clip” in the Device chooser and “Transposition” in the Control chooser. You can now
alter the pitch transposition of individual notes in the sample as you listen to it.

The fast way to do this is by enabling Draw Mode and drawing steps along the grid. Deactivate Draw
Mode to edit breakpoints and line segments. This is useful for smoothing the coarse steps by
horizontally displacing breakpoints.

The Transposition Envelope with Steps (Top) and Ramps (Bottom).

Note that the warp settings determine how accurately Live’s time-warping engine tracks the envelope
shape. To obtain a more immediate response, reduce the Grain Size value in Tones or Texture Mode,
or choose a smaller value for the Granulation Resolution in Beats Mode.

To correct the tuning of individual notes in the sample, hold down the Shift modifier while drawing
or moving breakpoints to obtain a finer resolution.

To scroll the display, hold down the Ctrl
dragging.

Alt (Win) / Cmd

Option (Mac) modifier while

Pitch is modulated in an additive way. The output of the transposition envelope is simply added to the
Transpose control’s value. The result of the modulation is clipped to stay in the available range
(-48..48 semitones in this case).

24.2.3 Muting or Attenuating Notes in a Sample

Select “Clip” in the Device chooser and “Gain” in the Control chooser. By drawing steps in Draw
Mode or creating shapes with breakpoints, you can impose an arbitrary volume shape onto the
sample.

Imposing a Volume Envelope on a Sample.

The volume envelope’s output is interpreted as a relative percentage of the Clip Gain slider’s current
value. The result of the clip envelope’s modulation can therefore never exceed the absolute volume
setting, but the clip envelope can drag the audible volume down to silence.

24.2.4 Scrambling Beats

One very creative use of clip envelopes is to modulate the sample offset. Sample offset modulation
makes the most sense for rhythmical samples, and is only available for clips that are set up to run in
the Beats Warp Mode.

Try sample offset modulation with a one-bar drum loop: Make sure Beats Mode is chosen; in the
Envelopes tab, choose “Clip“ from the Device chooser and “Sample Offset“ from the Control chooser.
The Envelope Editor appears with a vertical grid overlay. In envelope Draw Mode, set steps to non-
zero values to hear the loop scrambled. What is going on?

Imagine the audio is read out by a tape head, the position of which is modulated by the envelope. The
higher a value the envelope delivers, the farther away the tape head is from its center position.
Positive envelope values move the head towards the “future,“ negative values move it towards the
“past.“ Fortunately, Live performs the modulation in beats rather than centimeters: A vertical grid line is
worth a sixteenth note of offset and the modulation can reach from plus eight sixteenths to minus eight
sixteenths.

Sample offset modulation is the tool of choice for quickly creating interesting variations of beat loops.
We discourage using this technique for “analytical“ cut-and-splice tasks; they are much easier to
perform using Live’s Arrangement View, and the results can easily be consolidated into new clips.

Repeating Steps and Slowing Time with the Sample Offset Envelope.

Some sample offset envelope gestures have a characteristic effect: a downward “escalator“ shape,
for instance, effectively repeats the step at the envelope’s beginning. Similarly, a smooth ramp with a
downwards slope is slowing time and can create nice slurring effects when the slope is not quite
exactly 45 degrees; try this with a 1/32 Granulation Resolution.

24.2.5 Using Clips as Templates

As you are making creative use of clip envelopes, the clips containing them develop a life of their
own, independent of the original sample. You might wonder at a point: What does this clip sound like
with a different sample? This is easy to find out by selecting the clip so that it is displayed in the Clip
View and dragging the desired sample from the browser, or the Session or Arrangement View, onto
the Clip View. All clip settings, including the envelopes, will remain unaltered; only the sample will be
replaced.

24.3 Mixer and Device Clip Envelopes

Clip envelopes can be used to automate or modulate mixer and device controls. Since mixer and
device controls can potentially be controlled by both types of envelopes at the same time (and also
by the Arrangement’s automation envelopes, this is a potential source of confusion. However,
modulation envelopes differ from automation envelopes in one important way: Whereas automation
envelopes define the absolute value of a control at any given point in time, modulation envelopes can
only influence this defined value. This difference allows the two types of envelopes to work together in
harmony when controlling the same parameter. To help you distinguish between these, automation
envelopes are colored in red, whereas modulation envelopes are colored in blue. Additionally, in
parameters with knob controls, automation moves the absolute position (or the “needle”), whereas
modulation is indicated by the blue segment on the ring.

Imagine that you have recorded volume automation for an audio clip so that it gradually fades out
over four bars. What happens to your fade-out when you create a modulation envelope that
gradually increases the mixer volume over four bars? At first, your fade-out will become a crescendo,
as the modulation envelope gradually increases the volume within the range allowed by the
automation envelope. But, once the decreasing automated value meets with the increasing
modulation envelope value, the fade-out will begin, as automation forces the absolute control value
(and the operable range of the modulation envelope) down.

Both automation and modulation clip envelopes are available for clips in the Session View. A toggle
beneath the envelope choosers allows you to switch between editing automation and modulation clip
envelopes for the selected parameter. In the Arrangement, clips only have modulation envelopes,
while the automation envelopes reside on the track’s automation lane.

Toggle Between Editing Automation and Modulation Envelopes.

In a clip, parameters that have an automation envelope are indicated by a red LED in the Control
chooser. Similarly, parameters that have a modulation envelope are indicated by a blue LED. Some
parameters may have both red and blue LEDs, indicating that they are being automated and
modulated by the clip.

LEDs Indicate Existing Automation and Modulation Envelopes for the Selected Parameter.

24.3.1 Modulating Mixer Volumes and Sends

Notice that there are actually two modulation envelopes that affect volume: Clip Gain and Track
Volume. The latter is a modulation for the mixer’s gain stage and therefore affects the post-effect
signal. To prevent confusion, a small dot below the mixer’s volume slider thumb indicates the actual,
modulated volume setting.

Modulating the Mixer Volume. The Little Dot Below the Volume Slider Thumb Represents the
Modulated Volume Setting.

As you raise and lower the Volume slider, you can observe the dot following your movement in a
relative fashion.

Modulating the track’s Send controls is just as easy. Again, the modulation is a relative percentage:
The clip envelope cannot open the send further than the Send knob, but it can reduce the actual send
value to minus infinite dB.

Modulating a Send. The Blue Segment of the Send Knob’s Position Ring Indicates the
Modulated Value.

24.3.2 Modulating Pan

The Pan modulation envelope affects the mixer pan stage in a relative way: The pan knob’s position
determines the intensity of the modulation. With the pan knob set to the center position, modulation by
the clip envelope can reach from hard left to hard right; the modulation amount is automatically
reduced as you move the pan knob towards the left or right. When the pan knob is turned all the way
to the left, for instance, the pan modulation clip envelope has no effect at all.

24.3.3 Modulating Device Controls

All devices in a clip’s track are listed in the Device chooser. Modulating device parameters works
similarly to modulating mixer controls. When modulating device controls, it is important to keep in
mind the interaction between modulation and automation envelopes: unlike a device preset, the clip
envelope cannot define the values for the devices’ controls, it can only change them relative to their
current setting.

24.4 MIDI Controller Clip Envelopes

Whether you are working with a new MIDI clip that was recorded directly into Live, or one from your
files, Live allows you to edit and create MIDI controller data for the clip in the form of clip envelopes.

Choose “MIDI Ctrl“ from a MIDI clip’s Device chooser and use the Control chooser next to it to select
a specific MIDI controller. You can create new clip envelopes for any of the listed controllers by
drawing steps or using breakpoints. You can also edit clip envelope representations of controller data
that is imported as part of your MIDI files or is created while recording new clips: names of controllers
that already have clip envelopes appear with an adjacent LED in the Control chooser.

Live supports most MIDI controller numbers up to 119, accessible via the scroll bar on the right side of
the menu. Note that devices to which you send your MIDI controller messages may not follow the
conventions of MIDI control assignments, so that “Pitch Bend“ or “Pan,“ for example, will not always
achieve the results that their names imply.

A MIDI Controller Clip Envelope.

Many of the techniques described in the following section on unlinking a clip envelope from its
associated clip can be adapted for use with MIDI controller clip envelopes.

24.5 Unlinking Clip Envelopes From Clips

A clip envelope can have its own local loop/region settings. The ability to unlink the envelope from its
clip creates an abundance of exciting creative options, some of which we will present in the rest of this
chapter.

24.5.1 Programming a Fade-Out for a Live Set

Let us start with a straightforward example. Suppose you are setting up a Live Set and wish to
program a fade-out over eight bars to occur when a specific audio clip is launched — but all you
have is a one-bar loop.

Using a Clip Envelope to Create a Fade-Out Over Several Repetitions of a Loop.

1.
2.

3.
4.

5.

Choose the Clip Gain or Mixer Track Volume envelope, and unlink it from the sample.
The clip envelope’s loop braces now appear colored to indicate this envelope now has its own
local loop/region settings. The loop/region controls in the Envelopes tab “come to life.“ If you
toggle the envelope’s Loop switch, you’ll notice the Clip tab/panel’s Loop switch is not
affected. The sample will keep looping although the envelope is now playing as a “one-shot.”
Type “8“ into the leftmost envelope loop-length value box.
Zoom the envelope display out all the way by clicking on the Envelope’s time ruler and
dragging upwards.
Insert a breakpoint at the region end and drag it to the bottom.

Now, as you play the clip, you can hear the one-bar loop fading out over eight bars.

24.5.2 Creating Long Loops from Short Loops

Let us take this a step further. For a different part of your set, you would like to use the same one-bar
loop — because it sounds great — but its repetition bores you. You would like to somehow turn it into
a longer loop.

We depart from the clip we just set up to fade out over eight bars. Activate the clip volume envelope’s
Loop switch. Now, as you play the clip, you can hear the eight-bar fade-out repeating. You can draw
or edit any envelope to superimpose onto the sample loop. This, of course, not only works for volume
but for any other control as well; how about a filter sweep every four bars?

Note that you can create as much time as needed in the Envelope Editor, either by dragging the loop
braces beyond the view limit, or by entering values into the numeric region/loop controls.

You can choose an arbitrary loop length for each envelope, including odd lengths like 3.2.1. It is not
hard to imagine great complexity (and confusion!) arising from several odd-length envelopes in one
clip.

The Sample (Left) and Envelope (Right) Start Marker.

To keep this complexity under control, it is important to have a common point of reference. The start
marker identifies the point where sample or envelope playback depart from when the clip starts.

Note that the start/end markers and loop brace are subject to quantization by the zoom-adaptive
grid, as is envelope drawing.

24.5.3 Imposing Rhythm Patterns onto Samples

So far, we have been talking about imposing long envelopes onto small loops. You can also think of
interesting applications that work the other way around. Consider a sample of a song that is several
minutes long. This sample could be played by a clip with a one-bar volume envelope loop. The
volume envelope loop now works as a pattern that is repeatedly “punching“ holes into the music so
as to, perhaps, remove every third beat. You can certainly think of other parameters that such a
pattern could modulate in interesting ways.

24.5.4 Clip Envelopes as LFOs

If you are into sound synthesis, you may want to think of a clip envelope with a local loop as an LFO.
This LFO is running in sync with the project tempo, but it is also possible to set up a loop period odd
enough to render the envelope unsynchronized. By hiding the grid, you can adjust the clip envelope
loop start and end points independently of a meter grid.

The Stretch/Skew Envelope handles and automation shapes provide possibilities for designing
creative LFO shapes.

24.5.5 Warping Linked Envelopes

When in Linked mode, clip envelopes respond to changes in the clip’s Warp Markers. This means that
moving a warp marker will lengthen or shorten the clip envelope accordingly. Additionally, Warp
Markers can be adjusted from within the envelope editor.

Clip Envelopes and Warp Markers Can Be Adjusted Together.

25. Working with Video

Live’s flexible architecture makes it the perfect choice for scoring to video. You can trim video clips to
select parts of them and use Warp Markers to visually align music in the Arrangement View with the
video. You can then render your edited video file along with your audio.

Before diving in, you will want to be familiar with the concepts presented in the Audio Clips, Tempo,
and Warping chapter.

If you are interested in syncing Live with external video equipment, you’ll also want to read the
chapter on synchronization.

25.1 Importing Video

Live can import movies in Apple QuickTime format (.mov) to be used as video clips. Movie files
appear in Live’s browser and can be imported by dragging them into the Live Set.

Note that Live will only display video for video clips residing in the Arrangement View. Movie files that
are loaded into the Session View are treated as audio clips.

25.2 The Appearance of Video in Live

25.2.1 Video Clips in the Arrangement View

A video clip in the Arrangement View looks just like an audio clip, except for the “sprocket holes“ in its
title bar.

A Video Clip in the Arrangement View.

For the most part, video clips in the Arrangement View are treated just like audio clips. They can be
trimmed, for example, by dragging their right or left edges. However, there are some editing
commands that, when applied to a video clip, will cause it to be replaced by an audio clip (which by
definition has no video component). This replacement only occurs internally — your original movie
files are never altered. The commands which will cause this are: Consolidate, Reverse and Crop.

25.2.2 The Video Window

The Video Window in the Arrangement View.

The Video Window is a separate, floating window that always remains above Live’s main window. It
can be dragged to any location you like, and it will never get covered up by Live. You can toggle its
visibility with a command in the View menu. The Video Window can be resized by dragging its
bottom right-hand corner. The size and location of this window are not specific to the Set, and will be
restored when you open a video again. The video can be shown in full screen (and optionally on a
second monitor) by double-clicking in the Video Window. Hold Alt (Win) / Option (Mac) and
double-click in the Video Window to restore it to original size of the video.

25.2.2.1 Movies with Partial Tracks

In the QuickTime file format, the audio and video components do not have to span the entire length of
a movie; gaps in playback are allowed. During gaps in video, Live’s Video Window will display a
black screen; gaps in audio will play silence.

25.2.3 Clip View

Soundtrack composers will want to note the Tempo Leader option in Live’s Clip View. When scoring to
video, video clips are usually set as tempo leaders, while audio clips are left as tempo followers.
These are, therefore, the default warp properties of clips in the Arrangement View. In this scenario,
adding Warp Markers to a video clip defines “hit points“ that the music will sync to. Note that a video
clip’s Warp switch needs to be activated in order for the clip to be set as the tempo leader.

Setting a Video Clip as Tempo Leader.

Remember from the Audio Clips, Tempo, and Warping chapter that, although any number of warped
Arrangement clips can have the Tempo Leader option activated, only the bottom-most, currently
playing clip is the actual tempo leader.

This also means that it is possible for video clips that are not the current tempo leader to become
warped, resulting in warped video output in the Video Window.

25.2.3.1 Warp Markers

While dragging a Warp Marker belonging to a video clip, you will notice that the Video Window
updates to show the corresponding video frame, so that any point in the music can be easily aligned
with any point in the video clip.

Since Live displays a movie file’s embedded QuickTime markers, they can be used as convenient
visual cues when setting Warp Markers.

25.3 Matching Sound to Video

In Live, it takes just a few steps to get started with video. Let’s look at a common scenario — matching
a piece of music to edits or hit points in a video:

1.

2.

3.

4.

5.

6.
