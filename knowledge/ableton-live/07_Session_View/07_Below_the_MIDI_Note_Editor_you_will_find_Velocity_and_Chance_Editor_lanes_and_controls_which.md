---
id: 07
title: "Below the MIDI Note Editor you will find Velocity and Chance Editor lanes and controls which"
chapter: 07
---
# 7 Below the MIDI Note Editor you will find Velocity and Chance Editor lanes and controls which

7.

Below the MIDI Note Editor you will find Velocity and Chance Editor lanes and controls which
can be used to edit note velocities and probabilities. While only the Velocity Editor is shown by
default, you can toggle its visibility, as well as the Chance Editor’s visibility using the triangular
Lane Selector drop-down menu. The Show/Hide All Expression Editors toggle to the left of the
button allows showing or hiding all enabled lanes at once.

Show/Hide All Expression Editors Toggle.

It is also possible to choose whether Velocity or Chance Editor is shown in the visible lane using the
Swap Lane option available in the lane header’s context menu.

You can also drag the divider between the MIDI Note Editor and the Velocity and/or Chance Editor
lanes to resize or show/hide the lanes and controls. The lanes can be also resized individually via
their split lines. It is also possible to resize the lanes using the mousewheel/pinch gesture while
holding the Alt (Win) / Option (Mac) key.

8.

On the right side of the Clip View header, you can see the current grid setting and adjust the
grid properties via the chooser.

10.2 Zooming and Navigating in the MIDI Note

Editor

There are different ways of interacting with the MIDI Note Editor and its contents:

MIDI Note Editor Navigation.

1.

2.

3.

4.

To smoothly adjust the time zoom level, click and drag vertically in the time ruler. Drag
horizontally in the time ruler to scroll from left to right. While scrolling up and down inside the
MIDI Note Editor, you can also hold the Ctrl (Win) / Cmd (Mac) modifier to change the
time zoom level.
Scroll up and down in the note ruler to change which octaves are shown. Click and drag
horizontally in the note ruler to change the zoom level for key tracks, the MIDI notes they
contain and the piano ruler keys. While scrolling up and down inside the MIDI Note Editor, you
can also hold the Alt (Win) / Option (Mac) modifier to change the key tracks zoom level.
Click and drag over one or more notes to select them, or over an area in the MIDI Note Editor
to select a range of time. Then, double-click on the note ruler or time ruler to automatically
zoom in on your selection. Double-clicking on the note ruler will zoom in on the key tracks,
while double-clicking on the time ruler will zoom in on the selected time range. If nothing is
selected, double-clicking the note ruler will zoom in on the area from the lowest to the highest
note in the clip, while double-clicking the time ruler will zoom out to show the time between the
first and last note. Note that if you zoom in to the point when the time selection is no longer
displayed on the screen, double-clicking in the note ruler or time ruler will zoom out the MIDI
Note Editor so that the entire selection is in view.
The clip overview in the Clip View Selector in the bottom right corner of the Live window can
also be used for navigation. It always shows the complete contents of the selected MIDI clip.
The black rectangular outline represents the part of the clip that is currently displayed in the
MIDI Note Editor. To scroll, click within the outline and drag left or right; to zoom in and out,
drag up and down. You can also adjust the size of the outline by dragging its left or right
edges.

You can also use the computer keyboard to quickly navigate within the current selection MIDI Note
Editor. Use Page Up/Down keys to scroll vertically one octave up/down. Add the Shift modifier
to scroll vertically by just one key track up/down. To zoom in and out around the current time
selection, use the + and - keys. Zoom in fully into the current selection with the Z key. Zoom out
to view the full clip with the X key. Use Alt (Win) / Option (Mac) and + or - key to zoom
in to or out of the MIDI Note Editor.

As you work with MIDI, you may find yourself needing extra screen space. You can click and drag
vertically on the window split between the Session or Arrangement View and the Clip View to
increase the height of the Clip View and with it, also the size of the MIDI Note Editor.

Enlarge the MIDI Note Editor by Dragging the Window Split Between Session and Clip Views.

Clip View can be toggled to its maximum height using the Ctrl
E (Mac) keyboard shortcuts or the Expand Clip View entry in the View menu.

Alt

E (Win) / Cmd

Option

10.2.1 Grid Snapping

Most functions in the MIDI Note Editor are subject to grid snapping. This means that when you adjust
note positions, the grid acts as if it is magnetic: when you first move a note, it will move freely up to the
first grid line you encounter and afterwards, if you continue to drag the note, it will snap to grid lines
rather than move freely. You can bypass grid snapping by turning off the grid using the Grid Settings
button, by deactivating the Snap to Grid option in the Options menu, or by pressing the Ctrl
(Win) / Cmd
pressing the Alt (Win) / Cmd (Mac) modifier while performing editing operations. The opposite is
also true: if grid is disabled, it is possible to temporarily enable it using the same modifier.

4 (Mac) key combination. Grid snapping can also be bypassed temporarily by

Notes will also snap to an offset, which is based on the original placement of the note relative to the
grid. This is useful for preserving a groove or loose playing style that you do not necessarily want to
sound too “quantized.”

10.2.2 Playback Options

The MIDI Note Editor can be set to scroll with playback using the Follow switch in the Control Bar.
Follow will pause if you make an edit in the MIDI Note Editor, and will start again when you press the
Follow switch again, when you stop and restart playback, or when you stop playback and click in the
scrub area in the clip or the Arrangement View.

The Control Bar’s Follow Switch.

When Permanent Scrub Areas is enabled in Live’s Display & Input Settings, clicking in the scrub area
below the beat-time ruler starts playback from that point, rounded by the global quantization setting.

Activating the Options menu’s Chase MIDI Notes command allows MIDI notes to play back even if
playback begins after the MIDI note’s start time.

When the Permanent Scrub Areas preference is off, you can still scrub by Shift -clicking anywhere
in the scrub area or in the beat-time ruler. Learning about looping and scrubbing clips, and the
shortcuts associated with these actions can also be helpful in getting around in the MIDI Note Editor
and playing selections quickly and easily.

10.3 Creating a MIDI Clip

MIDI clips are created: - by recording on a MIDI track; - or by capturing MIDI; - or by double-
clicking an empty Session slot in a MIDI track; - or by selecting an empty Session slot in a MIDI track
and choosing the Create menu’s Insert Empty MIDI Clip(s) command, also accessible through the
Ctrl

M (Mac) keyboard shortcut; - or by double-clicking on
the track display of a MIDI track in the Arrangement View; - or, in the Arrangement View, by selecting
a timespan in a MIDI track and choosing the Create menu’s Insert Empty MIDI Clip(s) command, also
accessible through the Ctrl

M (Mac) keyboard shortcut.

M (Win) / Cmd

M (Win) / Cmd

Shift

Shift

Shift

Shift

10.4 Adding MIDI Notes

Notes are added to MIDI clips as you record yourself playing an instrument on an armed track, or
when you retrieve the material you played using the Capture MIDI option. You can also manually add
notes in the MIDI Note Editor by double-clicking in a chosen location or by drawing notes with the
mouse when Draw Mode is active.

The Control Bar’s Draw Mode Toggle.

10.4.1 Draw Mode

You can switch to Draw Mode by toggling the Control Bar’s Draw Mode button or by pressing the
B key. Once enabled, you click and drag inside the MIDI Note Editor to add notes. When Draw
Mode is active, clicking on an existing note will delete that note.

Adding New Notes Using Draw Mode.

There are two different ways of using Draw Mode: the “Draw Mode with Pitch Lock” option in the
Display & Input Settings lets you draw MIDI notes constrained to one single key track (or pitch) at a
time, while holding the Alt (Win) / Option (Mac) key allows freehand melodic drawing. When
disabled, Draw Mode defaults to freehand melodic drawing, and holding the Alt (Win) / Option
(Mac) key enables pitch-locked drawing. In the melodic Draw Mode, when you draw on top of an
existing note that note will be erased. In the pitch-locked Draw Mode, drawn notes will be erased
when you move the cursor back towards the first added note. When the MIDI Note Editor is focused,
the “Draw Mode” entry in the Options and context menus displays the currently selected state of the
“Draw Mode with Pitch Lock” preference, as “Draw Mode (Pitch Lock On/Off)”.

Draw Mode is useful for quickly adding in notes or patterns. When Draw Mode is switched off, you
can move notes around with the arrow keys or by clicking and dragging, either vertically to transpose
them, or horizontally to change their position in time. When Draw Mode is inactive, MIDI notes can
be deleted by double-clicking on them.

10.4.2 Previewing Notes

As long as your MIDI track’s device chain contains an instrument, activating the Preview switch in the
MIDI Editor allows you to hear notes as you add them or select and move existing notes. If the MIDI
track is armed, activating Preview also allows you to step record new notes into the clip. Note that the
Preview switch’s on/off state applies to all MIDI tracks in the Live Set.

Previewing MIDI Notes.

10.5 Editing MIDI Notes

Editing in the MIDI Note Editor is similar to editing in the Arrangement. In both cases, your actions are
selection-based: you select something using the mouse or computer keyboard, then execute a
command (e.g., Cut, Copy, Paste, Duplicate) on the selection.

10.5.1 Non-Destructive Editing

You can always return your MIDI clip to its previous state by using the Edit menu’s Undo command.
Furthermore, if the MIDI clip being edited originated in a MIDI file on your hard drive, none of your
editing will alter the original MIDI file, as Live incorporates its contents into your Live Set when
importing.

10.5.2 Selecting Notes and Timespan

Clicking in the MIDI Note Editor selects a point in time, represented by a flashing insert marker. You
can also move the insert marker to a specific location with the left and right arrow keys, according to
the grid settings. Holding the Ctrl (Win) / Option (Mac) key while pressing the left or right arrow
key moves the insert marker to the previous or next note boundary. The insert marker can be moved to
the beginning or end of a MIDI clip by pressing the Home or End key, respectively.

Clicking and dragging in the MIDI Note Editor selects a timespan. If the dashed line of the selected
timespan enclosed any notes, they will automatically also become selected. Press Enter to toggle

the selection between the timespan and any notes that are contained within it. Collapse the time or
note selection by clicking in the MIDI Note Editor outside of the selection or by pressing the Esc key.
You can also collapse time selection by using the arrow keys, which will move the insert marker. Note
that if you use the arrow keys with a note selection, the selected notes will be moved on the timeline
(when using left and right arrow keys) or transposed (when using up and down arrow keys).

You can also select a timespan using the computer keyboard. Hold down Shift while pressing the
arrow keys to select a timespan starting from the insert marker, according to the grid settings. Using
this combination with an existing time selection will extend or narrow the selection. Adding the Alt
(Win) / Cmd (Mac) key to the combination will extend or narrow the selection irrespective of the
grid settings. Holding Alt (Win) / Option (Mac) with Shift while pressing the arrow keys
extends or narrows the timespan to the next or previous note boundary.

You can select an individual note by clicking on it. You can also use the keyboard: place the insert
marker next to the note you want to select, then press Ctrl (Win) / Option (Mac) together with
the up or down arrow key to select a note nearest to the insert marker. Using the combination again
will change the selection to the next or previous note in time. To change the selection to the next note
in the same key track, hold Ctrl (Win) / Option (Mac) while pressing the left or right arrow keys.

Multiple notes can be selected by clicking and dragging in the MIDI Note Editor. You can add the
Shift modifier to add more notes to your current selection. You can also remove a single note from
your selection by holding down Shift and clicking on it. Holding Shift and clicking on the piano
ruler adds all notes in a single key track to the current selection, or removes them if they were already
selected. Click away from the selection in the MIDI Note Editor or press Esc to deselect the notes.

You can also select multiple notes with the keyboard by selecting a note, then pressing Ctrl
(Win) / Option
several times or hold it to continue adding to your existing note selection. The Ctrl
Cmd

Shift (Mac) in combination with the up or down arrow key. Use the shortcut
A (Win) /

A (Mac) keyboard shortcut selects all notes, while the Esc key deselects all selected notes.

Shift

If selecting multiple notes, but not all of the notes in the clip, it is possible to swap between the
currently selected notes and the unselected notes by using the Invert Selection command available
from the Edit menu or the MIDI Note Editor’s context menu. Alternatively, Ctrl
A (Mac) keyboard shortcut can also be used.
Cmd

Shift

Shift

A (Win) /

10.5.3 Find and Select Notes

You can search for notes that fulfill specific criteria using note selection filters. Notes found in this way
are automatically selected, which can be helpful for quickly editing multiple notes of a specific pitch
or duration, for example.

Find and Select Notes Using Filters.

To show the filters, enable the Find and Select Notes toggle in the Clip View header. You can select a
filter for finding and selecting notes using the chooser below the toggle. Each filter has a set of
dedicated controls, including the option to invert your search by selecting any notes not included in
the filter’s search criteria. It is also possible to combine multiple filters to create more precise note
selections.

You can filter by eight different note properties:

•

•

•

•

•

•

•

•

Pitch finds and selects the notes which have the pitch or pitches you specified via the Pitch
toggles. The filter finds notes in all octaves.
Time finds and selects notes within a specified time range. Use the Start and Length fields to set
the start point and length of the time range in beats, and the Repeat field to set the repetition
interval for the selected range in beats.
Chance finds and selects notes of the specified probability or within the specified probability
range, both of which can be set using the Min/Max Probability sliders.
Condition finds and selects notes that meet one of three conditions: Active, Chance, or Velocity
Deviation. When the Active toggle is enabled, all active notes are selected. When the Chance
toggle is enabled, all notes with probability values below 100% are selected. When the
Velocity Deviation toggle is enabled, all notes with velocity deviation are selected.
Count finds and selects every nth note or chord in a sequence. The Every slider specifies which
nth note to include in the selection. For example, when set to 2, every second note is selected.
You can use the Offset slider to adjust which note is considered the first in the selection. The
Quantized toggle groups selected notes according to the current grid settings. When active,
each group of notes located within a grid step counts as a value of 1 in the Every slider. For
example, when the Every slider is set to 3 and the Quantized toggle is active with a fixed grid
of 1/16, every third sixteenth note is selected.
Duration finds and selects notes of the specified length or within the specified duration range,
both of which can be set using the Min/Max Duration sliders.
Scale finds and selects notes that belong to the specified scale. When the filter’s Use Clip Scale
toggle is active, notes that fall within the current clip scale are selected. When the toggle is off,
you can specify a scale to filter notes with the Scale Root and Scale Name choosers.
Velocity — finds and selects notes of the specified velocity or within the specified velocity
range, both of which can be set using the Min/Max Velocity sliders.

A filter is applied and notes are automatically selected as you adjust the filter’s parameters; a yellow
dot also appears next to the filter name in the Filter chooser to indicate that the filter is currently
applied. To apply another filter, select it in the Filter chooser and adjust its parameters. To deactivate
all filters being applied by Find and Select Notes, click anywhere in the MIDI Note Editor. Note that
this deselects all notes.

Each filter includes two general controls: the Invert toggle and the Select button. When you activate
the Invert toggle, all notes that do not match the filter’s search criteria are selected. The Select button
selects all notes that match the current filter criteria and is useful for reapplying a deactivated filter
without adjusting its parameters.

When the Find and Select Notes toggle is active, you can use the mouse to adjust note selections
created with the filters. For example, you can press Shift and click on a key in the piano ruler to
add all of the notes in that key track to the selection. You can also produce evenly spaced repeated
time selections by pressing Shift , and then clicking and dragging left or right in the MIDI Note
Editor.

10.5.4 Moving Notes

Notes in the MIDI Note Editor can be moved both horizontally (changing their position in time) and
vertically (changing their transposition). They can be moved either by clicking and dragging, or with
the arrow keys on your computer keyboard. Notes will react to grid snapping unless the grid is off. To
nudge notes without snapping to the grid, hold Alt (Win) / Cmd (Mac) and press the left or right
arrow keys.

When notes are selected, you can use the Edit menu to perform editing actions on the notes, such as
Copy and Paste. Notes in the clipboard will be pasted starting at the location of the insert marker. You
can also use the Ctrl (Win) / Option (Mac) modifier to click and drag copies of notes to a new
location. If you click and drag to move notes but then decide that you would like to copy them
instead, you can press Ctrl (Win) / Option (Mac) even after you start dragging.

When editing or drawing, you may sometimes place a new note on top of one that already exists. If
the new note overlaps with the beginning of the original note, the original note will be overwritten. If
the new note overlaps with the end of the original, the original note will be shortened.

10.5.5 Changing Note Length

You can click on a note’s left or right edge and drag it to adjust the note’s length. As with note
positions, note lengths can be adjusted freely up to the previous or next grid line but will be quantized
when dragging further unless the Alt (Win) / Cmd (Mac) modifier is held down.

You can also change note length using the computer keyboard. Shift plus the left or right arrow
keys extends or shortens the duration of selected notes, according to the grid settings. To extend or
retract notes without snapping to the grid, also hold Alt (Win) / Cmd (Mac).

Changing Note Length.

You can extend the duration of all selected notes so that their start and end times match the current
time or note selection using the Fit to Time Range option or the Ctrl
Option

J (Mac) keyboard shortcut. The option is available as a command in the Edit menu or the
MIDI Note Editor’s context menu. You can also select the option from the Duration drop-down menu
in the Clip View’s Pitch and Time Utilities panel and apply it with the Set Length button.

J (Win) / Cmd

Alt

Fitting Notes into Time Range.

10.5.6 MIDI Note Stretch

MIDI Note Stretch Markers.

When multiple notes or a range of time are selected, Note Stretch markers will appear below the
scrub area, allowing notes to be scaled proportionally in time. The markers are a pair of downward-
pointing indicators that snap to the beginning and end of the selection.

By clicking and dragging one of the markers horizontally, the selected notes will be stretched in
proportion to their original lengths. Note Stretch markers can be freely moved until reaching the
previous or next grid or offset point, after which they will snap to the MIDI Note Editor’s grid lines
unless the grid is not shown or the Alt (Win) / Cmd (Mac) modifier is held while dragging.

When the mouse is between the Note Stretch markers, a “pseudo” stretch marker will appear.
Dragging this stretches or compresses the material between the fixed markers without affecting the
material outside of them. The pseudo stretch marker has the same grid snapping behavior as fixed
markers.

One Note Stretch marker can be dragged beyond the boundary of another, which will mirror the
order of the stretched notes in relation to their initial sequence.

Adjusting the Note Stretch markers will also adjust the timing of any of the clip’s linked clip envelopes.
Unlinked clip envelopes are not affected.

It is also possible to stretch notes using dedicated Stretch controls in the Clip View’s Pitch and Time
Utilities panel.

10.5.7 Deactivating Notes

To deactivate, or mute, a note (or notes), select it and press 0 , or use the Deactivate Note(s)
command in the Edit menu or in the piano ruler’s or the MIDI Note Editor’s context menu. When a
note is deactivated it is grayed out and will not be played. Press 0 again to reactivate notes.

10.5.8 Note Operations

There are several additional ways in which you can edit notes in the MIDI Note Editor: dividing notes
into two or more parts with the Split and Chop operations respectively, and combining separate notes
of the same pitch using the Join operation.

10.5.8.1 Split

The Split operation divides notes into two parts. To use Split, hold the E key, then draw a line across
notes to split them. You can also hold E and click and drag horizontally inside a note to
simultaneously split and adjust the split position.

Add the Ctrl (Win) / Cmd (Mac) modifier to snap the split position to the current grid.

Splitting Notes with a Mouse.

When no notes are selected you can also use the Ctrl
shortcut to split all notes intersecting with the insert marker or spanning beyond the time selection. You
can also use the Split Note(s) command from the Edit menu or the MIDI Note Editor’s context menu.
Note that the command is only available when at least one note intersects with the insert marker or
spans beyond the time selection.

E (Mac) keyboard

E (Win) / Cmd

10.5.8.2 Chop

The Chop operation can be used to divide notes into several parts based on the grid settings.

Chopping Notes.

There are different ways of chopping notes depending on whether you use a computer keyboard or a
mouse.

Chop notes using the keyboard: - Select notes and press the Ctrl
E (Mac) key
combination to chop the selected notes into parts based on the current grid settings. You can also use
the Chop Note(s) on Grid command from the Edit menu or the MIDI Note Editor’s context menu. -
Select notes, press the Chop shortcut, then continue holding the Ctrl (Win) / Cmd (Mac) modifier
and use the up and down arrow keys to increase or decrease the number of parts into which the notes
are chopped. Add the Shift modifier to increase or decrease the number of parts by a power of
two.

E (Win) / Cmd

Chop notes using the mouse: - Select notes, then press the E
key combination, hover over one of the selected notes and drag up or down to increase or decrease
the number of parts into which the notes are chopped. Add the Shift modifier to increase or
decrease the number of parts by a power of two.

Ctrl (Win) / E

Option (Mac)

Increasing the Number of Parts Into Which Notes Are Chopped.

10.5.8.3 Join

The Join operation creates one note from all selected notes of the same pitch, preserving MPE contents
and joining the MPE envelopes along with the MIDI notes.

To join notes, select notes in the same key track, then press the Ctrl
keyboard shortcut or use the Join Notes command from the Edit menu or the MIDI Note Editor’s
context menu.

J (Win) / Cmd

J (Mac)

The Join Notes Context Menu Command.

10.5.9 Pitch and Time Utilities

The Pitch and Time Utilities panel contains tools that offer a number of ways to quickly manipulate the
notes within a MIDI clip. These utilities affect the selected notes or a time range. If nothing is selected,
any changes applied with button controls will affect the whole clip.

10.5.9.1 Transpose

The Transpose slider displays the note pitch range. It can also be used to transpose a note or notes in
a time selection. Drag up or down in the slider or type a number into the slider to transpose notes by a
chosen number semitones or scale degrees (if a clip scale is active).

The Transpose Slider.

You can also transpose the selected notes directly in the MIDI Note Editor with the up and down
arrow keys. To transpose by octaves, hold down Shift while pressing the up or down arrow keys.

10.5.9.2 Fit to Scale

The Fit to Scale button adjusts pitches of the notes within the clip or the selection so that they fall within
the scale set for the clip. Notes are adjusted to the closest scale degree of a given scale or, in case of
an equal distance, to the lower scale degree. If a scale is not active for the clip, the button will be
greyed out.

The Fit to Scale Button.

10.5.9.3 Invert

Invert is a pitch operation where the position of the highest note is swapped with the position of the
lowest note, with other notes being flipped vertically, resulting in the note selection being turned
“upside-down”.

The Invert Button.

If a scale is active in the clip, Invert will calculate the inverse position of notes relative to the current
scale degrees.

Note: Invert is not to be confused with the Invert Selection option described in the Selecting Notes
and Timespan section earlier in this chapter: the former is a pitch change performed on a note
selection, whereas the latter changes what is selected.

10.5.9.4 Intervals

You can use the Interval Size slider and the Add Interval button to set the number of semitones or
scale degrees (if a clip scale is active) by which the pitches of new notes will be shifted in relation to
the pitches of the original note selection. This is useful for quickly creating chords.

If there is an existing note selection, adjusting the value in the Interval Size slider will result in new
notes being immediately added and selected in the MIDI Note Editor. When no notes are selected,
the slider merely sets the interval size which then needs to be applied with the Add Interval button. If
the button is then used with no note selection, new notes will be added at the specified interval for all
of the existing notes in the clip.

The Interval Size Slider and the Add Interval Button.

10.5.9.5 Stretch

It is possible to quickly adjust the note length of selected notes with the three note stretching options in
the Pitch and Time Utilities panel: the Stretch Factor control and the Double (×2) and Halve (/2)
buttons.

Stretch sets the factor by which the note length is changed. The ×2 and /2 buttons to the right of the
Stretch control respectively extend or shorten the note duration, time selection, or loop region by a
factor of 2.

Note Stretching Options.

Note that the Stretch control has no effect on the length of the loop region.

10.5.9.6 Note Duration

You can set the same note duration, or length, for all selected notes. It is possible to fit note lengths
within time range, use the current grid setting as the basis for note duration, or select a specific length
from the options available in the Duration drop-down menu.

Once you select the desired note length, apply it to the selected notes with the Set Length button. If no
notes are selected, pressing the button will apply the specified note length to all notes in the clip.

Note Duration Options.

10.5.9.7 Humanize

Humanize adds a variation to note starts times, removing any potential mechanical feel from the
composition. The variation percentage is set using the Humanize Amount slider, up to a quarter of a
grid division before or after the original note position, and can be applied with the Humanize button.

Humanize Options.

10.5.9.8 Reverse

The Reverse button rearranges the selection so that the position of the last note is swapped with the
position of the first note and the positions of the notes in between are flipped horizontally. When no
notes are selected, the entire clip is reversed.

The Reverse Button.

10.5.9.9 Legato

Pressing the Legato button results in the duration of each selected note being extended (or shortened),
so that it reaches the start of the next note. The last note gets extended to the end of the loop.

The Legato Button.

You can also use the Span MIDI Tool to apply legato note lengths.

10.5.10 MIDI Tools

The MIDI Tools contained in the Transform and Generate panels offer additional ways of editing MIDI
notes. Existing notes can be altered through, amongst others, articulation, interpolation, or
ornamentation, or completely new note patterns can be instantly generated according to specified
parameters.

You can find out more about all the available options for transforming and generating notes in a
dedicated MIDI Tools chapter.

10.5.11 Quantizing Notes

There are four ways of quantizing MIDI notes in Live:

1.
2.
3.

Quantizing notes as you record them.
Quantizing notes by moving them so that they snap to the visible grid lines.
Quantizing notes by using the Quantize MIDI Tool in Clip View’s Transform panel for more
granular control of note quantization. The transformation allows you to set a specific value at
which notes will be quantized (including the possibility of note starts and ends being

quantized). You can also quantize notes without giving them that “quantized” feel using the
Amount control, which will move notes only by a percentage of the set quantization value.

The Quantize MIDI Tool.

4.

Quantizing by selecting a note or notes and choosing the Quantize command from the Edit
menu, or using the Ctrl
U (Mac) keyboard shortcut. This option will use
the quantization settings as specified in the Quantize MIDI Tool described above. These settings
can also be opened using the Ctrl
U (Mac) keyboard
shortcut.

U (Win) / Cmd

U (Win) / Cmd

Shift

Shift

10.5.12 Editing Velocities

Note velocity data is recorded when a MIDI note is played as a result of pressing a key or a pad on a
controller and can be understood as a note’s loudness. In the MIDI Note Editor, note velocity is
visually indicated by the amount of saturation in the note’s color — less saturated notes play softly,
while more saturated notes play louder. You can use the Velocity Editor to adjust the velocity values
for the notes in a clip.

To change velocity for a MIDI note, click and drag on the associated marker in the Velocity Editor.
Velocity values will be shown numerically in the Velocity Editor’s lane header. To help you locate the
velocity marker belonging to a MIDI note that may be stacked vertically with others, Live highlights the
velocity marker for whichever note your mouse is hovering over.

Note Velocity Marker.

You can select multiple velocity markers to change by clicking with the Shift modifier held down.
To set a group of notes so that they all have the same velocity, select their markers in the Velocity
Editor, drag them up or down to either maximum or minimum velocity, and then adjust velocity to the
desired value.

To change the velocity of notes without opening the Velocity Editor, click any selected note and drag
vertically while pressing the Alt (Win) / Cmd (Mac) modifier.

Velocity values can also be entered manually by first selecting the velocity marker, then typing the
numerical value on the computer keyboard and hitting the Enter key.

You can use the up or down arrow keys with Ctrl (Win) / Cmd (Mac) held down to increment the
values of selected velocity markers by +/-10. Holding the Shift key at the same time allows fine-
tuning the values of selected velocity markers.

Apart from manually adjusting velocity values for notes, you can also set a velocity range or
randomize the note velocity values using Velocity Controls available below the Editor lanes when the
Velocity Editor is selected.

Velocity Controls.

Velocity values for selected notes (or notes with selected markers) can be randomized by clicking on
the Randomize button. If no notes or markers are selected, values for all notes will be randomized.

The Randomize Button.

The Randomization Amount slider to the right of the Randomize button allows specifying a range of
randomized velocity values. Velocities will be randomly increased or decreased by a value between
zero and the number shown in the slider. The slider’s value can also be typed as a number with the
keyboard, and randomization is then triggered when the new value is validated using the Enter
key.

The Randomization Amount Slider.

The Ramp sliders can be used to create a velocity ramp for multiple notes. The Ramp Start Value slider
is used to set the velocity value for the first note in the selection, whereas the Ramp End Value slider
sets the value for the last note. The other notes in the selection are distributed evenly within the range
set by the Ramp sliders.

The Ramp Sliders.

The Velocity Deviation slider can be used to set a range for each note’s velocity. Velocity values are
then chosen randomly from within the specified range each time a note is played. Positive and
negative values can be set, which increase or decrease velocity, respectively. For example, if a
velocity range of +20 is set for a selected note with a velocity value of 60, a random value between
60 and 80 will be chosen each time the note is played.

The Velocity Deviation Slider.

The velocity range is indicated by the shaded area that appears above or below the velocity markers
and with a dot inside of the velocity markers. Double-clicking the velocity marker which has a velocity
range set will reset the range to 0.

Velocity Markers with Deviation Set.

If multiple notes are selected, the range in the Velocity Deviation slider will be adjusted accordingly to
the existing velocity values. For example, when increasing the velocity range, if one note’s velocity
value is set to 50 and another note’s to 25, the velocity range of the first note can be +77 at most,
whereas the range of the second note can be +102. Both values will then be displayed in the slider to
reflect this.

The Velocity Deviation Slider with Varied Ranges of Deviation.

You can also set the velocity range by holding Ctrl (Win) / Cmd (Mac) and dragging up or
down from a velocity marker. This applies both to individual notes and a note selection.

10.5.12.1 Drawing Velocities

Draw Mode allows drawing inside the Velocity Editor as a way of setting velocity values instead of
adjusting them manually. You can enable Draw Mode by toggling the Control Bar’s Draw Mode
button or by pressing the B key.

Drawing velocity affects notes located within a given grid division will be affected. If the notes are
selected, only those notes will be affected, even if there are other notes within the grid division. If no
notes are selected, all notes will be affected. The exact notes that will be affected are highlighted in
blue when hovering over the Velocity Editor.

To draw markers individually (as you would want to with a crescendo, for instance) deactivate grid
snapping with the Ctrl
(Win) / Cmd (Mac) modifier. To draw markers along a straight line hold down the Alt (Win) /
Option (Mac) and drag the cursor. Add Shift to make the line horizontal.

4 (Mac) shortcut, or simply hold down the Alt

4 (Win) / Cmd

Drawing Identical Velocities (Left) and a Crescendo (Right).

To draw a velocity ramp with notes that are all in the same key track, click a key in the piano ruler to
select all notes within the desired key track and draw the ramp into the Velocity Editor.

10.5.12.2 Note Off Velocity

While the Velocity Editor allows you to adjust Note On velocities, you can also open the Release
Velocity Editor to show Note Off velocities.

Select the Release Velocity Editor via the Lane Selector.

Note Off (or “release”) velocity is a somewhat esoteric parameter. If you think of velocity as the
speed of pressing a key, you can look at release velocity as the speed at which the pressed-down key

is released. Release velocity is only supported by certain devices. Live’s Sampler instrument, for
example, provides Note Off velocity as a controller for a variety of parameters.

10.5.13 Editing Probabilities

Note probability determines the likelihood of a MIDI note being triggered during clip playback. You
can set probability for notes using the Chance Editor.

The Chance Editor.

Note that the Chance Editor lane is hidden by default and can be shown by clicking on the triangular
Lane Selector drop-down menu to the right of the Show/Hide All Expression Editors toggle on the left
of the Clip Content Toolbar.

To change a MIDI note’s probability value between 0-100%, click and drag on the note’s probability
marker in the Chance Editor. To help you locate the probability marker belonging to a MIDI note that
may be stacked vertically with others, Live highlights the probability marker for whichever note your
mouse is hovering over. As you drag the marker, the current probability value will be displayed in the
Chance Editor’s lane as well as the Status Bar. If multiple notes with different probability values are
selected, a range of probability values will be shown.

Note probability values can also be entered manually with a computer keyboard by first selecting a
probability marker, then typing the numerical value on the keyboard and pressing the Enter key.
Using the up or down arrow keys on the keyboard changes the values of selected probability markers
by +/-10%. Holding the Shift key while using the arrow keys allows fine-tuning the values of the
selected probability markers.

A small triangle is displayed in the upper-left corner of notes with probability values less than 100%.
The triangle is only visible if the key track height is expanded enough; otherwise, it will be hidden. To
increase the key track height, click and drag right in the note ruler and the MIDI Note Editor will zoom
in.

It is possible to randomize note probability values within a specified range, relative to the initial note
probability value. This range is set using the Randomization Amount slider in Clip Content Toolbar and
can help in creating variations on each loop for added interest or in humanizing the piece.

The Randomize Amount Slider.

Note probability will be randomly changed from the original value, with the new value falling on
either side of the initial probability, within the range set in the Randomization Amount slider. For
example, if the original probability value was 50% and the Randomization Amount was set to 25%,
the randomized probability values will range from 25-75%. When notes are selected, adjusting the
percentage in the slider will immediately randomize probability values for those notes. You can also
type in a value to set the randomization range using the keyboard, and apply the new range using the
Enter key. If no notes are selected, changing the value in the slider will have no effect until the
Enter key is pressed or the Randomize button is used, at which point the randomization will be
applied to all note probabilities.

The Randomize Button.

10.5.13.1 Probability Groups

In addition to setting a probability value for individual notes, you can also assign a single probability
value to a group of notes, so that either all notes in the group play according to the assigned value or
just one note out of the group plays at a time. These two probability group types are available:

Play All — all notes are played with the probability value set with a probability marker. Play One —
only one note in the group is played at a time, according to the set probability. The note which plays is
selected at random.

To create a note probability group, select the notes you would like to be a part of the group and press
either the Play All or Play One button in the Clip Content Toolbar, depending on the type of
probability group you wish to create.

Play All and Play One Buttons.

Once grouped, a single probability marker will be displayed for the notes in the Chance Editor: the
marker will have a diamond handle for the Play All group type or a triangle handle for the Play One
type. Right-clicking on a group probability marker allows you to change the probability group type.
You can also change the group type using the Play All or Play One buttons in the Clip Content
Toolbar.

Apart from the dedicated buttons, you can create note probability groups in a few other ways: - Use
the context menu options Group Notes (Play All) or Group Notes (Play One) in the MIDI Note Editor.
- Use the Edit menu command Group Notes (Play All) or Group Notes (Play One). - Use the
keyboard shortcut Ctrl
type as the group last created through either the dedicated buttons or the context menu.

G (Mac). The shortcut will create a group of the same

G (Win) / Cmd

Hovering over a note that belongs to a group highlights all the notes within the group. When selected
notes belong to a probability group, the group’s type will be displayed in the Status Bar. If all notes
belong to the same group, the type is listed explicitly, otherwise it is marked with an asterisk.

The small triangle displayed in the upper-left corner of notes with probability values less than 100% is
always displayed when a note belongs to a probability group, even if the probability of the group is
set to 100%.

To remove a note from a probability group, select it, then use the Ungroup button in the Clip Content
Toolbar. Alternatively, adding a note to a different group will automatically remove it from its original
group. In order to remove a probability group altogether, select all the notes in the group, then press
Ungroup.

The Ungroup Button.

You can also use the Edit menu command Ungroup Notes, the shortcut Ctrl
Cmd

G (Mac), or right-click on a grouped note marker and select the Ungroup Notes

Shift

G (Win) /

Shift

option. After notes are ungrouped, individual probability markers will be displayed for each note in
the Chance Editor once again.

10.6 Folding and Scales

The MIDI Note Editor includes folding options, which can be used to hide selected rows, or key tracks,
in the editor. These options apply to all MIDI clips in the Set, meaning that the available rows in each
clip in your Set will differ, depending on which notes exist in that clip.

The first folding option is Fold to Notes, which can be used to immediately hide all key tracks that do
not contain MIDI notes. This is very useful when working with percussion kits, for example, which are
oftentimes mapped out along a keyboard in sections corresponding to percussion type (e.g., snares
grouped together two octaves down from hi-hat cymbals). When editing a MIDI file created by such
a mapping, sometimes only one or two of each type of percussion sound is used, and it becomes
unnecessary to view the entire keyboard range.

The Fold to Notes option can be activated by pressing the Fold button located in the Clip View
header, by pressing the F shortcut key while the MIDI Note Editor is in focus, or via the View menu
entry.

The Fold Button Extracts Key Tracks Containing Notes.

If Fold to Notes is activated on a track containing a Drum Rack, only rows containing MIDI notes are
displayed. If the option is inactive, the key tracks for drum pads that contain devices are shown in the
MIDI Note Editor.

If Scale Mode is enabled for a clip, notes belonging to the selected scale are highlighted in the piano
ruler. This is useful for seeing at a glance which notes belong to that scale, allowing you to easily write
melodies within the chosen scale. Scale Mode can be toggled with a dedicated button in the Main
Clip Properties panel in the Clip View or in the Control Bar. To the right of the Scale Mode button,
Root Note and Scale Name choosers allow setting a root note and scale for the selected clip(s).

A MIDI Clip’s Scale Mode Settings.

By default, key tracks belonging to the selected scale are indicated through a highlight on the piano
ruler’s keys. If you want an even more noticeable indicator of which key tracks belong to the current
scale, you can use the Highlight Scales option. When active, key tracks within the selected scale are
highlighted in the MIDI Note Editor alongside the highlighted piano ruler’s keys, while the root note is

indicated by a prominent highlight in the piano ruler. Scale highlighting can be toggled by pressing
the Highlight Scale button in the Clip View header, by pressing the K shortcut key while the MIDI
Note Editor is in focus, or via the Highlight Scales context menu and Options menu entry. Scale
highlighting is applied globally.

Key Tracks Belonging to the Selected Scale Are Highlighted.

When multiple clips with different scale settings are selected, any foreground clip will influence the
scale settings for newly created clips. If Scale Mode is disabled, newly-created MIDI clips will inherit
the most recently selected clip’s scale setting, but the scale will remain inactive.

You can set a preference for spelling a clip’s notes with flats, sharps, or both, via the piano ruler’s
context menu. When Scale Mode is not enabled, this setting applies to all notes, but when Scale
Mode is enabled, this preference only applies to notes which are outside of the chosen scale; notes
within the scale will maintain their proper accidentals. An additional “Auto” option automatically
selects flats or sharps based on the position of the root note in the circle of fifths. Note that it is also
possible to display the notes as MIDI note numbers instead of pitches.

Setting a Preference for Spelling a Clip’s Notes.

When a scale is active in a clip, another folding option becomes available: Fold to Scale, toggled by
pressing the Scale button in the Clip View header, by pressing the G shortcut key while the MIDI
Note Editor is in focus, or via the View menu entry. Activating the Fold to Scale option will immediately
hide all key tracks that do not belong to the scale specified for the clip. Note that if you have already
added notes on the key tracks that don’t belong to the active scale, those key tracks will still be
displayed, even when the Fold to Scale option is active.

This option is useful as a melodic composition reference for selecting complimentary notes. It can be
especially helpful if you are not confident in your knowledge of music theory and want to compose
melodies without constantly adjusting note placement until the sound “feels right.”

Key Tracks Belonging to the Current Scale Displayed After Pressing the Scale Button.

10.7 Editing MIDI Clips

Apart from editing individual notes in a clip, there are also operations that apply to the entire MIDI
clip. Many of these are covered in the Clip View chapter, but there are additional ways of working
with MIDI clips described below.

10.7.1 Cropping MIDI Clips

MIDI data that is outside of the loop brace can be deleted using the Crop Clip command. If there is a
time selection, the MIDI data outside of the selection can be deleted with the Crop to Time Selection
command instead. Simply right-click on a MIDI clip in the Session or Arrangement View and select the
J (Win) / Cmd
relevant option, or use the Ctrl

J (Mac) keyboard shortcut.

Shift

Shift

Note that unlike cropping samples in audio clips, cropping a MIDI clip does not create a new file on
disk.

10.7.2 The …Time Commands in the MIDI Note Editor

The standard clipboard commands like Cut, Copy and Paste only affect the currently selected notes
(or the notes within a time selection). But, as in Arrangement editing, there are “… Time” commands
that act upon the entire MIDI clip by inserting and deleting time.

Note that these operations do not change the clip start/end position or the loop brace settings.

•

•

•

Duplicate Time places a copy of the selected timespan into the clip, along with any contained
notes.
Delete Time deletes a selection of time from the MIDI clip, thereby moving any notes on either
side of the deleted area closer together in the timeline.
Insert Time inserts as much empty time as is currently selected into the clip, before the selection.

10.7.3 Looping

When editing MIDI, you might find that you want to loop a specific portion of a clip in order to make
fine adjustments while listening to the section repeatedly. You can use the loop markers for this.

You can select a region for looping by moving the position of the loop start and end markers. Note
that it is possible to adjust the looping region during playback.

Use the Loop/Region Markers to Select a Specific Region of the Clip to Play.

Selecting the loop brace in a MIDI clip and pressing Ctrl
the length of the loop brace, duplicates the notes contained within the original loop brace, and zooms
out as necessary to show the entire loop. Any notes to the right of the loop will be moved, so that they
maintain their position relative to the end of the loop.

D (Mac) doubles

D (Win) / Cmd

MIDI clips are looped by default. You can turn off looping for an individual clip using the Clip Loop
toggle in the Clip View’s Main Clip Properties panel. When looping is switched off, the loop brace is
grayed out.

Looping Switched Off for a Clip.

10.8 Multi-Clip Editing

In the MIDI Note Editor, you can view and access notes in multiple MIDI clips at the same time. This
helps you to see melodic and rhythmic relationships between different clips when creating and
refining musical ideas, and allows you to edit material across separate tracks and scenes more
quickly. In addition to editing notes across multiple clips, you can also modify various parameters for
the selected clips.

While multi-clip editing is useful for looking at clips across different tracks, it can also come in handy
when you need to compare and edit multiple clips within the same track. For example, you can create
evolving pattern progressions by adding notes to a clip, then making a variation to the clip in the
following scene and so on, while maintaining an overview of the other clips in the track.

When multiple MIDI clips are selected:

•

•

The notes from these clips will be shown together in the MIDI Note Editor. You can select and
edit notes from multiple selected clips at the same time, or use Focus Mode to edit notes in a
single clip while notes from other clips are still in view.
Loop bars will appear above the MIDI Note Editor. Each loop bar represents a different clip in
the current selection, and the colors of the loop bars match the color of the clip. Clicking on a
clip’s note or loop bar switches to that clip for editing.

Multi-Clip Loop Bars in the MIDI Note Editor.

•

•

•

•

•
•

•

You can adjust the loop length for any single clip by clicking and dragging its loop bar marker.
You can also select and edit loop bars from any of the selected clips simultaneously, by clicking
or dragging their loop markers while pressing the Ctrl (Win) / Cmd (Mac) key. Using the
Shift key allows you to select contiguous loop bars. Note: With Focus Mode enabled, it is
not possible to select more than one loop bar at a time, and any existing multi-selection is
ignored.
You can duplicate selected loop bars using the context menu option or the Ctrl
Cmd

D (Win) /

D (Mac) keyboard shortcut.

The title bar will show the name of the clip selected for editing. This can be particularly useful for
identifying different clips with the same color. Note: If a clip has no name, the title bar will
display the name of the track containing the clip instead.
Certain controls in the Clip View panels are editable for all selected clips. These controls
include loop, time signature, groove, and scale settings.
Fold to Notes and Fold to Scale can be used for all selected clips.
Actions in Velocity or Chance Editor are only ever applied to a single clip at a time. The
velocity and probability markers are displayed for the foreground clip, not for all clips. It is not
possible to make changes to velocity or probability for all notes in all selected clips.
You can resize the height of the loop bars by clicking and dragging vertically directly above the
multi-clip title bar’s scrub area.

Note that multi-clip editing works differently depending on whether you are working in the Session
View or in the Arrangement View.

10.8.1 Focus Mode

Focus Mode allows you to select a single clip to edit while viewing multiple clips. Focus Mode can be
toggled via the Focus button or the N keyboard shortcut. Holding N while editing with the mouse
toggles Focus Mode momentarily. Multi-clip editing functions differently depending on whether Focus
Mode is enabled or not.

The Focus Button Toggles Focus Mode.

When Focus Mode is enabled:

•

•

•
•

•

•

•

The active clip’s notes will be shown in that clip’s color, while the inactive clips’ notes will be
shown in gray.
The active clip’s loop bar will be shown in the clip color, while the inactive ones will be shown
in gray. Whenever clicked, the active clip’s loop bar will be shown in black. You can click away
from the loop bar anyway on the active clip’s timeline to return the clip’s loop bar to the clip
color while maintaining the clip in focus.
The name of the active clip is displayed below the loop bars.
Hovering the mouse over an inactive clip’s loop bar will reveal that clip’s color and notes,
helping you to choose a different clip in the current selection to edit. Clicking on a clip’s note or
loop bar switches to that clip for editing.
Any clip and note editing operations available in the Clip View in the MIDI Note Editor are
only available for editing the active clip.
The scale displayed in the Clip View is the scale of the currently selected clip. This scale affects
the Fold to Scale option.
Enabling Fold to Notes will fold all key tracks outside all the selected clips.

When Focus Mode is disabled:

•
•

All notes are displayed with their clip’s color, as all notes are active.
A clip’s loop bar will turn black when clicking on it, which then allows you to randomize
Velocity or Chance for notes within that clip by first-clicking. The non-selected loop brace will
display the color of its clip.

•

•

•

•

•

The root note and scale name for the currently selected clips are only displayed in the Clip View
if they are the same across all clips. Otherwise, an asterisk is shown where different root notes
or scale names are chosen.
Any clip and note editing operations available in the Clip View in the MIDI Note Editor are
available for all selected clips.
Notes can be cut or copied from multiple clips and inserted into the same set of clips, as long
as the clip selection/foreground clip has not changed, or into a different clip once that new clip
has been selected.
Note editing functions (e.g. copy, cut, paste, delete) can be used when working with note
selections across clips and loop boundaries.
Time in the MIDI Note Editor can be selected across loop and clip boundaries.

10.8.2 Multi-Clip Editing in the Session View

In the Session View, you can select and view up to eight MIDI clips at the same time, all of which must
be looped. In the MIDI Note Editor, loop bars are ordered vertically (first by track, and then by
scene).

If multiple clips of different lengths are selected, the MIDI Note Editor will show as many loop
iterations as necessary for the clips to realign. The part of the timeline that falls outside of a clip’s loop
area will be marked in a darker version of the clip color. When you hover over a clip, loop start and
end will be represented by black vertical lines in the MIDI Note Editor. If a clip’s start marker is set
before the loop start, the loop markers for the clip will be shifted accordingly to represent this.

10.8.3 Multi-Clip Editing in the Arrangement View

In the Arrangement View, it is possible to select and view MIDI clips from up to eight tracks, across a
selection of time. In the MIDI Note Editor, loop bars are ordered vertically by track and horizontally
by time.

Notes can be drawn continually across clip boundaries, except in Focus Mode.

The MIDI Note Editor will not show silence before or after the selection of clips – instead, it will fit its
display range to show the beginning of the first clip up to the end of the last clip in the selection. If the
selection contains looped and unlooped clips, the Loop button in the Clip View will appear half
colored.

11. MIDI Tools

MIDI Tools open further possibilities when it comes to working with MIDI content. These scale-aware
utilities can be accessed via the Transform and Generate panels of the Clip View. While
Transformations are aimed at performing targeted operations on existing MIDI notes, Generators offer
more exploratory tools, resulting in the creation of new material.

Transformation Tools modify various note properties of existing notes, including MPE data. They
require a selection of notes as input for the transformation.

MPE MIDI Tools are a subset of Transformations and can be used to add note expression or transform
existing expression data. You can view the results of applying these MIDI Tools in the MIDI Note
Editor’s MPE view mode.

Generative Tools do not use any input and instead add new notes to the clip loop or time selection.
Note that if there are already notes in the clip or time selection, the generated notes will replace the
existing notes.

Transformations and Generators are further divided into native MIDI Tools and Max for Live MIDI
Tools. Native MIDI Tools are built into Live and their properties cannot be edited. In contrast, the
bundled Max for Live MIDI Tools can be edited, and you can also build additional MIDI Tools or
install MIDI Tools from third-party creators to further expand your toolset for note transformation and
generation. The Max for Live MIDI Tools you built or saved can be quickly located in the browser with
a dedicated MIDI Tools filter group or the MIDI Tool tag in the Content filter group.

11.1 Using MIDI Tools

In order to transform notes or generate notes using a MIDI Tool, open the Transform or Generate
panel, select a tool from the Transformation/Generator Selector chooser and tweak the settings in the
selected MIDI Tool’s interface. By default, the Auto Apply button is active for all MIDI Tools. This
means that MIDI notes will be transformed or generated immediately when adjusting a MIDI Tool’s
settings.

The Auto Apply Button.

Any subsequent changes to a MIDI Tool’s parameters will be visible in the MIDI Note Editor straight
away. If you do not wish for the Transformations and Generators to have an immediate effect, toggle
off the Auto Apply button. Note that toggling the button off will restore notes to their original state.

With the Auto Apply button toggled off, you can fine-tune a MIDI Tool’s parameters and, once you’re
happy with the settings, press the Apply button for the adjustments to take effect.

The Apply Button.

You can also apply the currently selected MIDI Tool without leaving the MIDI Note Editor by pressing
Ctrl

Enter (Win) / Cmd

Enter (Mac).

Transformations are applied to the time selection, note selection, or clip loop (when there is no time or
note selection). When using Transformations, the existing notes get replaced with the transformed
notes.

Generators are applied to the time selection or clip loop (when there is no time selection). If there are
already notes present in the MIDI Note Editor when a Generator is applied, the generated notes will
be added alongside the existing content (if the existing notes and the generated notes don’t overlap)
or will replace the existing notes (if the existing and generated notes overlap).

Since MIDI Tools are scale-aware, if a scale is enabled for a clip, any MIDI Tools’ parameters related
to pitch will use scale degrees instead of semitones.

The transformation or generation of notes can be undone and redone with the Undo and Redo
commands in the Edit menu. Note that these commands only affect changes made to MIDI notes and
not changes made to a MIDI Tool’s parameters. You can restore the parameters to their default state
with the Reset button. The button becomes grayed out when the MIDI Tool is reset to default.

An Active Reset Button.

The Reset button only applies to the parameters in the selected MIDI Tool and has no effect on the
MIDI notes.

11.2 Transformation Tools

Below you will find a list of all MIDI Transformations included in Live.

11.2.1 Arpeggiate

The Arpeggiate Transformation splits up the note selection into arpeggiated notes based on the
chosen pattern settings. It uses the core functionalities found in the Arpeggiator MIDI effect.

The Arpeggiate MIDI Tool.

The Style drop-down menu allows you to select an arpeggiated sequence which will be applied to
the selected notes. The Arpeggiate Transformation offers the same 18 style patterns known from
Arpeggiator.

The Distance control determines the transposition of steps in the pattern using scale degrees or
semitones, depending on whether a scale is set for the clip.

The Steps slider allows you to select the number of transposed steps in the pattern.

The Rate and Gate controls determine how notes are distributed on a timeline: the former sets the rate
of the pattern (which also affects note length), while the latter affects note duration. When Gate is set
to values below 100%, notes will be shortened, whereas at values above 100% notes will be
lengthened.

Notes Before and After Applying the Arpeggiate Transformation.

11.2.2 Chop

The Chop Transformation divides selected MIDI notes into a maximum of 64 parts. It can also be used
to design note division patterns; for example, you can create a pattern where some notes are
extended relatively to others, or where a random variation is added to note start or end times.

The Chop MIDI Tool.

You can create a note chopping pattern by setting the number of parts for the chopped note(s) with
the Parts control, from 2 to 64 parts. The Gaps control adds spaces to the pattern, with the exact
minimum and maximum number of gaps depending on the number of parts the pattern contains.
When set to positive values, the control represents the number of notes after which a gap will be
added. When set to negative values, the control represents the number of gaps that will be added
after each note. For example, when set to 2, a gap replaces a note in the sequence after two
successive notes. When set to -2, two gaps are added after each note. Note that a pattern can consist
of a maximum of 16 parts. If the Parts control is set to a higher value, the pattern will repeat.

The Pattern toggles visualize the pattern designed with the Parts and Gaps controls and let you
manually add and remove gaps within the pattern, which can be helpful in creating rhythmic
variations. When the number of gaps is changed with the Pattern toggles, the Gaps control shows a
dash. If the control is adjusted, the manually added gaps in the pattern are replaced with those set
through the Gaps control.

The Emphasis toggles let you select which notes or gaps are emphasized in the pattern. Emphasized
pattern elements are affected by the Stretch Chunk(s) value, which stretches the relative length of notes
or gaps from 2 to 8 times longer. When notes or gaps are emphasized, their corresponding Pattern
toggles are grayed out.

You can use the Variation slider to add random variation to the note start and end times.

Notes Before and After Applying the Chop Transformation.

11.2.3 Connect

The Connect Transformation generates new notes that fill the gaps between existing notes. The
placement of the interpolated notes is randomized, but some particulars of the pattern can be
determined using Connect’s parameters.

The Connect MIDI Tool.

The Spread control sets the maximum random pitch shift of the connecting notes based on the original
note pitches, in scale degrees or semitones.

Density allows you to specify the percentage of the time interval between original notes to be filled
with interpolated notes. At 100%, all the gaps between existing notes will be filled.

Use the Rate control to set the length of the interpolated notes and the Tie control to determine the
probability that the length of a generated note will be extended to the next original note.

Notes Before and After Applying the Connect Transformation.

11.2.4 Glissando

The Glissando Transformation is an MPE MIDI Tool that connects the pitch of one note to the pitch of a
successive note along a pitch bend curve, tying the notes together. At least two notes must be selected
to create a glissando.

The Glissando MIDI Tool.

The Start control sets the starting point of the pitch bend curve, expressed as a percentage of the note
length. The Curve control changes the shape of the pitch bend curve. You can click and drag the
yellow breakpoint in Glissando’s display left or right to adjust pitch bend start, or click and drag the
line up or down to adjust the pitch bend curve shape.

Notes Before and After Applying the Glissando Transformation.

Note that you can only view the pitch bend curve in the MPE Editor. When the MIDI Note Editor is
open, the Glissando Transformation is applied, but the pitch bend curve is not visible.

When working with folded notes, you can display the pitch bend curve below the MIDI Note Editor
by activating the Pitch Bend expression lane.

Pitch Bend Curve Displayed in a Dedicated Expression Lane.

11.2.5 LFO

LFO is an MPE Transformation that uses a low-frequency oscillator to set the value of one of three
MPE parameters: pitch bend, slide, or pressure. The oscillator’s shape, rate, and global amplitude can
all be customized using the Transformation’s parameters.

The LFO MIDI Tool.

The Target chooser lets you set Pitch Bend, Slide, or Pressure as a modulation target for the LFO. The
LFO curve display shows the shape of the LFO used as a modulation source.

The Envelope Attack and Decay sliders set the attack and decay of the oscillator’s amplitude
envelope, relative to the total length of the oscillation. Note that the envelope’s attack and decay
values influence each other. This means that if, for example, Attack is set to 100%, Decay is
automatically reset to 0%.

The Shape control adjusts the shape of the oscillator based on the shape selected in the Shape Type
chooser. You can choose from the following four types: Sine, Square, Triangle, or Random. When
Random is selected, the Reseed button can be used to generate new random shapes for the LFO.

The Reseed Button.

The Rate control sets the period of the oscillator in musical time, from 1 to 1/128. For example, setting
the rate to 1 equates to 4 beats. The Time Shift slider below Rate shifts the LFO in time. Positive values
delay the start of the oscillation and negative values adjust its phase.

The Amount control sets the oscillator’s amplitude. When Pitch Bend is selected as the modulation
target, Amount can be set to any value within double the clip’s current pitch bend range. For example,
if the range is set to ±60 st, Amount can be set from -120 st to 120 st. When Slide or Pressure are
selected, Amount can be set from -127 to 127. You can set the base value for the amplitude using the
Amplitude Base slider below the Amount control. When Pitch Bend is selected as a modulation target,
Amplitude Base can be set to any value within the clip’s current pitch bend range. For example, if the
range is set to ±60 st, Amplitude Base can be set from -60 st to 60 st. When Slide or Pressure are
selected, Amplitude Base can be set from -127 to 127.

Notes Before and After Applying the LFO Transformation.

The MPE curve for the Pitch Bend modulation target is displayed in the MIDI Note Editor. You can also
choose to display it below the MIDI Note Editor by activating the Pitch Bend expression lane, which
can be helpful when working with folded notes. Modulation curves for Slide and Pressure are
displayed in their respective expression lanes.

Note that the modulation applied by the LFO Transformation is only displayed in the MPE Editor.
When the MIDI Note Editor is open, the Transformation is applied, but the expression curves are not
visible.

11.2.6 Ornament

The Ornament Transformation contains Flam and Grace Notes options which allow for ornamental
notes to be added to the beginning of selected notes. Reapplying the Transformation to the same
selection results in additional flam or grace notes being inserted.

The Ornament MIDI Tool.

Select which type of ornamental notes to add by switching on either the Flam or Grace Notes toggle.

The Flam and Grace Notes Toggles.

When using Flam, a single note is added to the beginning of each selected note.

The Flam Position parameter controls the placement of the flam note: at positive values, the flam note
will replace the beginning of the original note, while at negative values, the flam note is prepended to
the start of the selected note. The parameter’s value represents the percentage of the current grid
setting, so the length of the flam note will be determined by the grid size rather than the length of the
original note. This means that at 100% / -100% the flam note’s length will be equal to one grid
division, placed respectively at the start of the original note or before it, and will become
proportionally shorter as Flam Position’s value approaches 0%.

The Flam Velocity parameter sets the velocity of the flam notes relative to the velocity of the original
notes.

Notes Before and After Adding Flam.

When using Grace Notes, multiple notes of equal length are added to the beginning of each original
note.

The Grace Notes Pitch buttons allow you to determine the pitch of the added grace notes relative to
the original note. When High is selected, every other grace note is placed one semitone (or scale
degree, if a scale is active) higher than the original notes, while when Low is selected, the pitch of
every other grace note is one semitone or scale degree lower than the existing notes. If Same is
selected, the grace notes are added at the same pitch as the original notes.

The Grace Notes Position parameter controls whether the added grace notes replace the beginning of
the selected notes (when the parameter is set to positive values) or are prepended to the original notes
(at negative values). The value represents the percentage of the current grid size: at 100% / -100%
the inserted graces notes will fill one grid division, placed respectively at the start of the original note
or before it.

The Grace Notes Velocity parameter determines the velocity of grace notes relative to the velocity of
the original notes.

The Grace Notes Chance control determines the probability that each grace note will be played
relative to the original note’s Chance values.

The Grace Notes Amount parameter allows you to specify the number of grace notes to be applied to
each selected note. The individual grace notes are always equivalent in size.

Note Selection Before and After Adding Grace Notes.

11.2.7 Quantize

The Quantize MIDI Tool adjusts the timing of selected notes by moving or stretching them according to
the specified quantization settings. Note that an equivalent Quantize tool exists for audio clips.

The Quantize Transformation.

You can transform notes according to the current grid size or set a specific meter value for
quantization (including triplets). It’s possible to quantize note start or end time, or both note start and
end time simultaneously. Quantizing the note end will stretch the note so that it ends at the chosen
meter subdivision. You can also quantize notes without giving them that “quantized” sound using the
Amount control, which will move notes only by a percentage of the set quantization value.

Notes Before and After Applying Quantization.

Aside from navigating to the Transformation using Clip View’s tabs/panels, you can also open the
Quantize MIDI Tool to change its parameters by using the Quantize Settings… command in the Edit
menu, or use the Ctrl
to the selected notes without opening the Transform tab/panel.

U (Mac) shortcut to apply quantization

U (Win) / Cmd

Shift

Shift

11.2.8 Recombine

The Recombine MIDI Tool rearranges the position, pitch, duration, or velocity for a selection of notes,
so that a parameter value set for one note in the selection is applied to a different note.

The Recombine Transformation.

You can use the Dimension chooser to select one of four note parameters for Recombine to permute:
Position, Pitch, Duration, or Velocity.

The Dimension Chooser.

There are three ways of rearranging note parameters using Recombine: 1. Shuffle, where note
parameters are permuted randomly. 2. Mirror, where note parameters are permuted to be in reverse
order to the note selection. 3. Rotate, where note parameters are permuted in a circular way.

The Shuffle and Mirror permutation types can be activated using their respective toggles, whereas for
Rotate to take effect, you need to set the number of Rotation Steps to a value other than 0.

Rotation Steps can be set by clicking and dragging your mouse across the columns in Recombine’s
display or by using the Rotate Step Down/Up buttons below the display. The number of available
steps is always one step fewer than the number of selected notes. Positive numbers rotate parameter
values clockwise, and negative numbers rotate parameter values counter-clockwise.

When Position is selected in the Dimension chooser, you can switch on the Rotate on Grid toggle.
When on, Recombine uses the number of grid cells in the selection as a basis for the number of
available Rotation Steps rather than the number of notes. The exact number of available Rotation
Steps depends on the current grid settings.

Each permutation type can be used individually or in conjunction with others. Permutation types are
applied in the following order: Shuffle, then Mirror, then Rotate. Note that when Shuffle is active, a
new parameter permutation is created each time the Apply button is pressed.

Note Velocities Before and After Applying the Shuffle Transformation Mode.

11.2.9 Span

The Span MIDI Tool transforms the durations of selected notes using three articulation types: legato,
tenuto and staccato.

The Span Transformation.

It is also possible to introduce some variety to how notes are transformed with additional parameters:

•

•

Offset adjusts note end times up to a grid step. At positive values, note length is extended; at
negative values, note length is shortened.
Variation adds random variation to note lengths. At positive values, note length is shortened; at
negative values, note length is extended. If set to values other than 0%, new note length
variation will be produced whenever the Transformation is reapplied.

Legato extends the length of selected notes to the start time of the next note in the sequence. The last of
the selected notes will be extended to the end of the time selection or, if there is no time selection, to
the end of the loop.

Notes Before and After Applying Legato.

Tenuto preserves the original note length unless the Offset and Variation parameters are adjusted.

When using the Staccato articulation type, note length is determined by the distance between start
times of the selected notes. The smallest distance between start times is halved and this duration is
used as the new note length for the transformed notes. Note length can be further modified using the
Offset and Variation parameters.

11.2.10 Strum

The Strum MIDI Tool adjusts the start times of notes in a chord following a shape set by the Strum Low,
Strum High and Tension parameters.

The Strum Transformation.

The Strum Low parameter determines the offset of the successive notes, starting with the lowest note. At
positive values, the note start times are moved forward, whereas at negative values the start times are
moved back. The start time of the lowest note is offset up to one grid step at 100% / -100%. The other
notes are proportionally, matching the shape in the Strum Position display. If the Tension parameter is
set to 0.0%, notes are distributed at an equal distance between each other.

The Strum High parameter determines the offset of the original chord starting with the highest note.
When set to positive values, the note start times are moved forward, whereas at negative values the
start times are moved back. The highest note is offset up to a grid step at 100% / -100%. The other
notes are distributed proportionally to match the shape in the display. If the Tension parameter is set to
0.0%, notes are distributed at an equal distance between each other.

In order for the Transformation to have effect, the Strum Low and/or Strum High parameters must be
set to a value other than 0.0%. You can make changes to both parameters by adjusting their
respective breakpoints in the Strum Position display, or by entering a value for each using your
computer keyboard.

The Tension parameter changes the offset of note start times so that they are no longer placed at an
equal distance between each other, but instead alongside a curve, with distances between notes
being larger or smaller, depending on the settings. At positive Tension values, the distance between
the notes will be greater at the start of the note sequence and decrease exponentially. At negative
values, the distance between notes at the start of the sequence will be shorter and increase
exponentially.

Notes Before and After Applying the Strum Transformation.

11.2.11 Time Warp

Time Warp is a time-stretching MIDI Tool that transforms selected notes according to a speed curve.
This allows creating tempo variations such as accelerando or ritardando.

The Time Warp Transformation.

You can create the speed curve in the Breakpoints display. The time range of the curve is mapped to
the time selection. It is possible to enable between one and three breakpoints in the speed curve using
their respective toggles. You can either drag a breakpoint in the display or select it and use the
Breakpoint Time and Breakpoint Speed sliders to set the breakpoint’s timeline position and speed,
respectively. The sliders’ values always reflect the values of the currently selected breakpoint.

The toggles below the Breakpoints display allow you to make further adjustments to the time-warping
applied. When Quantize is on, the warped notes will be quantized according to the grid settings.
When the Preserve Time Range switch is enabled, the results of the Transformation will fit within the
same range as the original note selection. When the Include Note End switch is toggled on, the end
positions of the original notes are taken into account when applying the speed curve, which will have
an effect on the duration of the original notes.

Notes Before and After Applying Time Warp.

11.2.12 Velocity Shaper

Velocity Shaper is a Max for Live Transformation.

The Velocity Shaper MIDI Tool.

Velocity Shaper allows you to shape the velocities of selected notes using an adjustable envelope.

The envelope shape in the display will influence how the velocities of the selected notes are
transformed. Click in the display to add more breakpoints to the envelope and drag them to adjust the
envelope shape.

You can use the Minimum and Maximum Velocity parameters on the right of the display to define the
velocity range for the transformed notes.

The Loop parameter below the display sets the number of times the envelope shape will be applied to
the note selection.

The Rotate control determines the number of steps the envelope shape is offset, relative to the start of
the note selection. The size of the step is determined by the Division parameter. For example, if Rotate
is set to 1 and Division is set to “Grid”, the envelope shape will be shifted to the right by one grid step.

Notes Before and After Applying Velocity Shaper.

11.3 Generative Tools

Below you will find a list of all MIDI Generators in Live.

11.3.1 Rhythm

The Rhythm MIDI Tool generates a note pattern according to the set parameters, repeated to fill a
given time selection.

The Rhythm Generator.

The notes can be generated for a particular pitch or for an individual drum pad when working with
Drum Racks. You can choose a pitch or a drum pad using the Pitch control, or by holding the Alt
(Win) / Option (Mac) key and clicking on the piano ruler.

Use the Steps control to set the number of steps in the pattern, up to 16 steps.

The Pattern knob is used to determine the placement of the generated notes (the shape of the pattern).
The number of available patterns depends on the values set for the Steps and Density parameters.

The Density knob controls the number of notes in a pattern. Note that the maximum value is
determined by the number set with the Steps control.

The Step Duration slider can be used to adjust the number of times a pattern is repeated in the time
selection. For example, for a time selection of one bar, if Step Duration is set to 1/8 and Steps is set to
8, the pattern will be repeated only once. When Step Duration is changed to 1/16 in the same
scenario, the pattern is repeated twice. Note that Step Duration will affect the maximum number of
steps to be set using the Steps control.

The Split control allows you to set a probability for a step in a pattern to be divided in half.

Shift moves the generated notes by a specified number of steps to the right when set to positive values
and to the left when set to negative values.

You can set the note velocity for the generated notes and specify a different velocity for accented
notes using the Velocity and Accent sliders. The number of accented notes that occur in the pattern is
determined by the Accent Frequency parameter, which sets the number of notes between accented

notes. This value ranges from 0 to the number of notes specified by the Density parameter. Note that
an accented note is counted as a note occurrence — if the Accent Frequency is set to 1, every note
will be accented. You can use the Accent Offset arrows to shift the placement of accented notes in the
pattern.

To add to your rhythmic pattern, deselect the previously generated notes and adjust Rhythm’s
parameters again for a different pitch or drum pad.

A Rhythmic Pattern Generated in a Drum Track.

11.3.2 Seed

The Seed MIDI Tool randomly generates notes within specified pitch, length and velocity ranges.
Additional parameters allow specifying the number of simultaneously occurring notes, as well as the
overall number of generated notes.

The Seed Generator.

To select the range of pitches within which new notes will be generated, drag the Minimum and
Maximum Pitch or Key Track sliders or the triangular handles in the Pitch Range slider. If one of the
handles is dragged to overlap the other, the handles get merged; in this case, notes will be generated
in one pitch only. To revert to two handles, click anywhere in the Pitch Range slider or set different
values in the Minimum and Maximum Pitch or Key Track sliders. You can also hold the Alt (Win) /
Option (Mac) key and click in the piano ruler to select a single pitch for notes to be generated in or
click and drag to select a range of pitches. Note that if the clip has an active scale, the slider will be
displayed in purple; otherwise, it will be displayed in the same color as the other two sliders.

The Duration and Velocity Range sliders work in the same way as the Pitch Range slider to set note
length and velocity ranges for generated notes. The minimum note length you can set for the duration
range is 1/128 note and the maximum is one note. Velocity can range from 1 to 127.

You can also control the number of notes added using the Voices and Density controls, which allow
setting the maximum number of simultaneous notes to be generated, as well as the number of all
generated notes, represented as a percentage of the pitch range to be populated.

Notes Added Using Seed.

11.3.3 Shape

Shape is a MIDI Tool that generates a sequence of notes within a range of pitches. The notes are
distributed following a shape defined in the MIDI Tool’s display.

The Shape Generator.

In order to determine the shape that will be used for note generation you can use the Shape Presets
drop-down menu or draw your own shape in the display. Use the Minimum and Maximum Pitch
sliders to set a range in which the notes will be added. You can also hold the Alt (Win) / Option
(Mac) key and click and drag to select a range. Note that when a clip scale is active, the shape is
displayed in purple.

Use the Rate control to set the minimum length of the generated notes. Note duration can also be
affected by the Tie parameter, which sets the probability that a generated note will be extended to the
next note.

The Density knob allows you to set the number of notes to be added, represented as a percentage of
the shape to be populated.

If you want to randomize the pitches of the generated notes, use the Jitter parameter. At 0%, the notes
will follow the shape set out in the Shape Levels display exactly and will move progressively further
away from the shape as you increase the Jitter value. Note that the randomized pitches will always
stay within the range specified by the Minimum and Maximum Pitch sliders.

Notes Generated with Shape.

11.3.4 Stacks

Stacks is a MIDI Tool you can use to add individual chords or create chord progressions within a
selected scale. The generated chords fill time selection or the length of the loop if there is no time
selection.

The Stacks Generator.

You can select a chord pattern by clicking and dragging the Chord Selector Pad or using Ctrl
(Win) / Cmd (Mac) and the up and down arrow keys. The chord pattern diagrams are simple
illustrations of the relationship between the intervals in a chord; they are based on the Tonnetz system.
When hovering over a Chord Selector Pad, additional information about the chord is displayed in the
Status Bar.

You can also load custom chord banks into Stacks. Chord banks are text files in the JSON format. To
load a chord file into the Stacks Generator, place a .stacks file in a folder that’s added to the
browser’s Places section, then double-click the file name to load it as a replacement for Stacks’s
default chord bank. You can quickly locate the chord files later by using the browser’s dedicated
Stacks tag in the MIDI Tool filter group, or the MIDI Tool tag in the Content filter group. Find out more
about creating custom chord banks in this Knowledge Base article.

To create a chord progression, use the Add Chord plus button to the right of the Chord Selector Pad/s
and select a pattern for the additional chords. You can reduce the number of chords using the Delete
Chord minus button.

Use the Chord Root knob to set the root note for the chord. You can also hold the Alt (Win) /
Option (Mac) key and click in the piano ruler to make the selection, or use up and down arrow keys

to cycle through root notes. If there is a scale set for the clip, the Chord Root will be automatically
adjusted to the root note of that scale. You can still choose a different root note for the chord, but
whenever a clip scale is active, the root note options for the chord will be limited to the notes within
the clip scale.

The Chord Inversion knob allows you to rearrange a chord using one of the available inversions.
Positive values cycle through the possible inversions for a selected chord and negative values cycle
through the same inversions an octave lower. Chord Duration and Offset can be used to set the length
and position of a chord. Both can be adjusted in eighths of the original chord length.

Note that all of the parameters visible in the Stacks Generator’s display at a given moment are
specific for the currently selected chord. This means that whenever another chord is selected, the
display will be updated to show that chord’s parameters.

Chord Progression Generated with Stacks.

11.3.5 Euclidean

Euclidean is a Max for Live Generator.

The Euclidean MIDI Tool.

Euclidean generates notes based on Euclidean rhythms for up to four voices at a time. New notes will
be generated within the time selection or, if there is no time selection, within the loop.

The Pattern tab contains a visual representation of how generated notes will be added to the clip. To
the right of the visualization, there are individual toggles that can be used for activating and
deactivating voices, as well as individual Rotation sliders for setting the offset of generated notes for
each voice, relative to the beginning of the time selection. In the middle of the pattern visualization,
there is a randomization button, which sets the Rotation sliders’ value for each voice at random.

You can click on Voices to select the Voices tab. Like in the Pattern tab, there are toggles to activate or
deactivate individual voices, as well as the option to set each voice to a specific pitch (when using
instrument devices) or drum pad (when using Drum Racks). Use the up and down arrows to the left of
the voice activation toggles to simultaneously change all the pitches or drum pads used to generate
notes. You can also set individual velocity values for the notes generated for each voice using the
Velocity sliders on the right.

Below the Pattern and Voices tabs, there are additional parameters that can be used to further define
the shape of the generated rhythmic pattern:

Steps — Determines the length of the generated pattern. If the pattern length is shorter than the length
of the time selection, the pattern will be repeated and potentially wrapped around the time selection.
Density — Determines the number of times the pattern is repeated within a time selection. If the pattern
doesn’t fit within the time selection, notes will be wrapped around the time selection. Division — Sets
the length of a step in the pattern.

Notes Generated with the Euclidean MIDI Tool.

12. Editing MPE

MIDI Polyphonic Expression (MPE) is an extension to the MIDI specification that enables attaching
parameter control information to individual notes, instead of globally per MIDI channel. This way of
using MIDI allows MPE-capable devices to control multiple parameters of every note in real time for
more expressive instrumental performances.

To enable Live to receive per-note expression from an MPE-capable MIDI controller, first enable MPE
Mode in the Link, Tempo & MIDI Settings for that controller.

Enabling MPE Mode for a MIDI Controller.

Note that when selecting a MIDI controller that has MPE enabled as an input device on a track, the
channel input routing is fixed to “All Channels’’ and no individual channels can be selected.

For more information about working with MIDI controllers, please refer to the MIDI and Key Remote
Control chapter. Once your controller is set up, you can use it to record new MIDI clips containing
MPE data.

The Clip View’s Note Expression tab allows viewing and editing five dimensions of MPE for each note
in a clip: Pitch (per-note pitch bend), Slide (per-note Y-Axis), Pressure (Poly Aftertouch/MPE

Pressure), Velocity and Release Velocity (Note Off Velocity). This makes it possible to refine the
expression of recorded material, or to automate polyphonic sound variations for MPE-capable
instruments.

Note that you can view and edit MPE data for notes in all MIDI clips, regardless of whether those
clips were created using an MPE-capable device or using other methods. We will look at viewing and
editing MPE data in the following sections.

12.1 Viewing MPE Data

A MIDI Clip with MPE Data in the Clip View.

To view MPE data in a MIDI clip, first enter Clip View by double-clicking on a clip, then click on the
3 (Mac) to open the
Note Expression Tab or use the key command Alt
Expression Editors at the bottom of Clip View. Four of the five MPE parameters are contained in their
own expression lane: Slide, Pressure, Velocity, and Release Velocity. By default, only Slide and
Pressure are shown. Envelopes for the fifth parameter, Pitch, are displayed on top of their
corresponding notes in the MIDI Note Editor.

3 (Win) / Option

Each expression lane can be shown or hidden via the lane selector toggle buttons at the left.
Underneath the lane selector toggle buttons, a triangular toggle button allows showing/hiding all
enabled lanes at once.

These Buttons Toggle Visibility of Expression Lanes.

When all expression lane selectors are hidden/disabled, pressing the triangular toggle button will
show all expression lanes at once. Each expression lane can be resized individually via their split
lines. All expression lanes can be resized simultaneously by dragging the split line between the lanes
and the MIDI Note Editor.

Pressing Alt (Win) / Option (Mac) and clicking the triangular toggle button displays all
expression lanes. When hiding the expression lanes using the triangular toggle button, or by dragging
the Expression Editor View split line, the lane visibility toggles are hidden as well.

MIDI track meters will display MPE per-note controller changes. The lowest dot in a meter lights up in
a blue color if per-note controller changes pass that meter.

12.2 Editing MPE Data

When clicking a note (or any of its expression dimensions) in the MIDI Note Editor while the Note
Expression tab is open, the note will appear in a transparent overlay. Envelopes appear, along with
any existing breakpoints, to allow editing the note’s Pitch, Slide, and Pressure envelopes, while
markers can be used to edit the note’s Velocity and Release Velocity values. Unselected notes will
appear grayed out, and their expression envelopes will be dimmed.

Select a Note to View Its Expression Envelopes.

After clicking on the note or envelope you wish to edit, all expression breakpoints for the chosen
envelope and the line segments connecting them become draggable objects. Clicking and dragging
in the envelope’s background defines a selection. Here’s how editing MPE data works:

•
•
•

Click at a position on a line segment to create a new breakpoint there.
Click on a breakpoint to delete it.
To help you edit breakpoints more quickly, expression values are shown when you create,
hover over, or drag a breakpoint. Note that when hovering over or dragging a selected line
segment, the expression value shown will correspond to the breakpoint value at the cursor’s
current position.

A Breakpoint’s Expression Value.

•

•

•

Click and drag a breakpoint to move it to the desired location. If the breakpoint you are
dragging is in the current selection, all other breakpoints in the selection will follow the
movement.
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

•

•

•

4 (Mac) shortcut. When the grid is enabled, breakpoints and line

In the Note Expression tab, the grid is disabled by default for easier editing at a finer resolution.
Note that the grid’s settings are separate from the grid in the other tabs, and they are saved
with the clip.
If needed, you can enable the grid using the Snap to Grid options menu entry or the Ctrl
4 (Win) / Cmd
segments will snap to time positions where neighboring breakpoints exist. Breakpoints created
close to a grid line will automatically snap to that line.
When moving a line segment or breakpoint, hold Shift while dragging to restrict movement
to either the horizontal or vertical axis.
Holding down the Shift modifier while dragging vertically allows you to adjust the
breakpoint or line segment value at a finer resolution.
You can remove a neighboring breakpoint by continuing to drag a breakpoint or line segment
“over” it horizontally.
Hold Alt (Win) / Option (Mac) and drag a line segment to curve the segment. Double-
click while holding Alt (Win) / Option (Mac) to return the segment to a straight line.

A Curved Envelope Segment.

•

Except for the Pitch expression envelope, you can scale Slide, Pressure, Velocity and Release
Velocity envelopes proportionally across a note’s entire duration, similar to that of velocities for

A (Win) / Cmd

multiple selected notes. To so do, first click outside of the note’s area, then hover the mouse
above the desired envelope. When the envelope turns blue, click and drag up or down, and
the envelope will be scaled accordingly. This is also the behavior when editing expression
envelopes for multiple selected notes at once.
You can also adjust all selected breakpoints equally, rather than scaling them. To do so, first
click on the envelope you wish to edit, then use Ctrl
A (Mac) to select
all of the breakpoints, then drag up or down with the mouse as desired to increase or decrease
their value; dragging left or right will move all breakpoints horizontally as a group.
When a note is moved, its expression envelopes will move along with it.
Stretching a MIDI note using the MIDI stretch markers in the MIDI Editor or the ÷2 and x2
buttons in the Notes tab will cause any per-note expression belonging to that note to be
stretched as well.
Pitch breakpoints snap to the nearest semitone when pressing Alt (Win) / Cmd (Mac) while
the grid is off. This also works for Pitch values in Draw Mode. This behavior can be bypassed
using the same shortcuts when the grid is on.
Pitch envelopes are hidden when Fold Mode is enabled in the Note Expression tab.
When the Note Expression tab is open, using the Zoom to Clip Selection command or Z key
shortcut adjusts the zoom level according to pitch bend values contained in the time selection.
When the Note Expression tab is open, the Clear All Envelopes entry in the context menu of the
MIDI Note Editor and per-note expression lanes clears all expression envelopes of one or
multiple selected notes.

•

•
•

•

•
•

•

12.3 Drawing Envelopes

With Draw Mode enabled, you can click and drag to free-handedly “draw“ an envelope in the Pitch,
Slide and Pressure expression lanes.

To toggle Draw Mode for MPE data, select the Draw Mode Option from the Option menu, click on
the Control Bar’s Draw Mode switch, or press B , then click on the envelope you wish to edit.
Holding B while editing with the mouse temporarily toggles Draw Mode.

Drawing an Envelope.

Holding down the Shift modifier while dragging vertically allows you to adjust the expression
value of a step at a finer resolution.

When the grid is enabled using the Snap to Grid options menu entry or the Ctrl
4 (Win) / Cmd
4 (Mac) shortcut, drawing creates steps as wide as the visible grid, which you can modify using a
number of handy shortcuts. To temporarily enable drawing in the grid while it is disabled, hold down
Alt (Win) / Cmd (Mac) while drawing.

12.4 MPE in Live’s Devices and on Push 2

Many Live devices support MPE and include MPE presets that bring new dimensions of interaction
and playability to your sound. The expressive possibilities within these devices also enable you to take
advantage of polyphonic aftertouch on Push 2.

12.5 MPE in External Plug-ins

MPE data for MPE-enabled plug-ins can also be accessed and modulated in Live.

The enabled/disabled state of a plug-in device’s MPE Mode will be saved with that device’s default
configuration.

Plug-ins that have MIDI outs and that have MPE enabled can also output MPE.

12.6 MPE/Multi-channel Settings

To set up a specific MPE configuration, you can access a MPE/Multi-channel Settings dialog box
from:

•
•
•

The Ext. Instrument device.
The I/O section of Live’s mixer.
The context menu of an MPE-enabled plug-in.

These settings can be used for hardware synths that require a specific MPE configuration, or plug-ins
that do not officially support MPE but can be used with MPE controllers due to their multi-timbral
support.

12.6.1 Accessing the MPE/Multi-channel Settings Dialog

In the Ext. Instrument device, you can choose your Routing Target in the MIDI To drop-down menu.
Then select MPE from the second drop-down, open the menu again, and select MPE Settings…

The MPE Settings in Ext. Instrument.

To access these settings in the I/O section of the mixer, make sure you have the device you want to
control selected in the MIDI To section of the MIDI track’s output and choose MPE from the MIDI To
drop-down menu in the Session or Arrangement Mixer, then open the drop-down menu again and
choose MPE Settings…

The MPE Settings in the I/O Section.

For MPE-enabled plug-ins, you can find these settings in the context menu of the respective device’s
title bar.

The MPE Settings in a Plug-in Context Menu.

12.6.2 The MPE/Multi-Channel Settings Dialog

The MPE/Multi-channel Settings.

You can use the settings to:

•

•
•

Configure the MPE zone and range of note channels used by Live when sending MPE to an
external MIDI device or plug-in.
Select the upper or lower zone and number of note channels.
Select multi-channel mode, which sets an arbitrary range of note channels.

There are settings available for the lower zone and upper zone. A track can only output to a single
zone, so to use both zones, set up two tracks.

Each zone needs a global channel (for non-polyphonic controls). The global channel for the lower
zone is Channel 1, and Channel 16 is for the upper zone. You can also assign a range of the other
MIDI channels to each zone (in general the number of channels you assign to a zone is linked to the
amount of polyphony you want in that zone). An example zone configuration might be to use
channels 1-11 for the lower zone and channels 12-16 for the upper zone.

Note: Live only supports zones for MPE output, which is particularly useful for hardware synths that
require a particular zone configuration.

These settings can also be used, for example, to connect two MPE synths to the same MIDI interface
(again, one connected through the MIDI thru of the other), or setting up a synth that knows how to
control two different sounds by assigning them to different zones. You can set up two MIDI tracks in
Live, routed to the same MIDI output device, but configuring one track for the lower zone and the
other for the upper zone.

13. Converting Audio to MIDI

Although Live’s warping allows for audio files to be used much more flexibly than in traditional audio
software, there are also a number of ways to extract musical information from audio clips and place it
into MIDI clips, for additional creative possibilities.

When an audio clip is selected, four conversion commands are available in the Create Menu or the
context menu for the clip.

Context Menu Commands For Converting Audio To MIDI.

13.1 Slice to New MIDI Track

This command divides the audio into chunks which are assigned to single MIDI notes. Slicing differs
from the Convert commands below, in that it doesn’t analyze the musical context of your original
audio. Instead, it simply splits the original audio into portions of time, regardless of the content. The
Drum Rack provides an ideal environment for working with sliced files, and most of the setup happens
automatically after you make a few choices:

The Slicing Dialog.

When you select Slice to New MIDI track, you’ll be presented with a dialog box. This offers a list of
slicing divisions, as well as a chooser to select the Slicing Preset. The top chooser allows you to slice at
a variety of beat resolutions or according to the clip’s transients or Warp Markers. Since a Rack can
contain a maximum of 128 chains, Live won’t let you proceed if your choice would result in more than
128 slices. You can fix this by either setting a lower slice resolution or by selecting a smaller region of
the clip to slice.

The Slicing Preset chooser contains a few Ableton-supplied slicing templates, as well as any of your
own that you may have placed in your User Library’s default presets folder.

With “Preserve warped timing” enabled, the clip will be sliced in such a way that timing alterations as
a result of warping are preserved. With this option disabled, any changes that result from warping will
not be reflected in the sliced clip; the sliced version will instead sound like the original, “raw” audio.

Once you’ve made your slicing choices and clicked OK, a number of things will happen:

1.

2.

3.

A new MIDI track will be created, containing a MIDI clip. The clip will contain one note for
each slice, arranged in a chromatic sequence.
A Drum Rack will be added to the newly created track, containing one chain per slice. Each
chain will be triggered by one of the notes from the clip, and will contain a Simpler with the
corresponding audio slice loaded.
The Drum Rack’s Macro Controls will be pre-assigned to useful parameters for the Simplers, as
determined by the settings in the selected slicing preset. In the factory Slicing presets, these
include basic envelope controls and parameters to adjust the loop and crossfade properties of
each slice. Adjusting one of the Macro Controls will adjust the mapped parameter in each
Simpler simultaneously.

Note: Live will take a few moments to process all of this information.

Playing the MIDI clip will trigger each chain in the Drum Rack in order, according to the timing
information that you specified or that was embedded in the audio. This opens up many new editing
possibilities, including:

13.1.1 Resequencing Slices

Rearranging the Sliced MIDI Data.

By default, your sliced MIDI data will form a chromatically-ascending “staircase“ pattern in order to
trigger the correct chains in their original order. But you can create new patterns by simply editing the
MIDI notes. You can achieve a similar effect by dragging the Drum Rack’s pads onto each other to
swap their note mappings.

13.1.2 Using Effects on Slices

Because each slice lives in its own chain in the Drum Rack, you can easily process individual slices
with their own audio effects. To process several slices with the same set of effects, multi-select their
chains in the Drum Rack’s chain list and press Ctrl
their own nested Rack. Then insert the effects after this new sub-Rack.

G (Mac) to group them to

G (Win) / Cmd

For even more creative possibilities, try inserting MIDI effects before the Drum Rack. The Arpeggiator
and Random devices can yield particularly interesting results.

Slicing is most commonly applied to drum loops, but there’s no reason to stop there. Experiment with
slicing audio from different sources, such as voices and ambient textures. The same sorts of
resequencing and reprocessing operations can be applied to anything you slice — sometimes with
unexpected results.

13.2 Convert Harmony to New MIDI Track

This command identifies the pitches in a polyphonic audio recording and places them into a clip on a
new MIDI track. The track comes preloaded with an Instrument Rack that plays a piano sound (which
can, of course, be replaced by another instrument if you choose).

Note that this command, as with the other Convert commands, differs from slicing in that the
generated MIDI clip does not play the original sound, but instead extracts the notes and uses them to
play an entirely different sound.

The Convert Harmony command can work with music from your collection, but you can also get great
results by generating MIDI from audio recordings of yourself playing harmonic instruments such as
guitar or piano.

13.3 Convert Melody to New MIDI Track

This command identifies the pitches in monophonic audio and places them into a clip on a new MIDI
track.

The track comes preloaded with an Instrument Rack that plays a synthesizer sound. Using the Rack’s
“Synth to Piano” Macro Control, you can adjust the timbre of this sound between an analog-style
synth and an electric piano. The instrument was designed to be versatile enough to provide a good
preview, but can of course be replaced with another instrument if you choose.

The Melody to MIDI Instrument Rack.

The Convert Melody command can work with music from your collection, but also allows you to
record yourself singing, whistling, or playing a solo instrument such as a guitar and use the recording
to generate MIDI notes.

13.4 Convert Drums to New MIDI Track

This command extracts the rhythms from unpitched, percussive audio and places them into a clip on a
new MIDI track. The command also attempts to identify kick, snare and hihat sounds and places them
into the new clip so that they play the appropriate sounds in the preloaded Drum Rack.

As with the Convert Melody command, you can adjust the transient markers in the audio clip prior to
conversion to determined where notes will be placed in the converted MIDI clip.

Convert Drums works well with recorded breakbeats, but also with your own recordings such as
beatboxing or tapping on a surface.

13.5 Optimizing for Better Conversion Quality

The Convert commands can generate interesting results when used on pre-existing recordings from
your collection, but also when used on your own recorded material. For example, you can record
yourself singing, playing guitar, or even beatboxing and use the Convert commands to generate MIDI
that you can use as a starting point for new music.

For the most accurate results, we recommend the following:

•

•

•

Use music that has clear attacks. Notes that fade in or “swell” may not be detected by the
conversion process.
Work with recordings of isolated instruments. The Convert Drums command, for example, works
best with unaccompanied drum breaks; if other instruments are present, their notes will be
detected as well.
Use uncompressed, high-quality audio files such as .wav or .aiff. Lossy data formats such as
mp3 may result in unpredictable conversions, unless the recordings are at high bitrates.

Live uses the transient markers in the original audio clip to determine the divisions between notes in the
converted MIDI clip. This means that you can “tune” the results of the conversion by adding, moving,
or deleting transient markers in the audio clip before running any of the Convert commands.

Although each of the commands has been designed for a particular type of musical material, you can
sometimes get very interesting results by applying the “wrong” command. For example, Convert
Harmony will usually create chords. So running it on a monophonic clip (like a vocal recording) will
often generate notes that weren’t present in the original audio. This can be a great way to spark your
creativity.

14. Using Grooves

The timing and “feel“ of each clip in your Set can be modified through the use of grooves. Live comes
with a large selection of grooves, which appear as .agr files in the browser.

Groove Files in the Browser.

The easiest way to work with library grooves is to drag and drop them from the browser directly onto
clips in your Set. This immediately applies the timing characteristics of the groove file to the clip. If you
want to quickly try out a variety of grooves, you can enable the Hot-Swap button above a clip’s Clip
Groove chooser and then step through the grooves in the browser while the clip plays.

The Hot-Swap Groove Button.

Grooves can be applied to both audio and MIDI clips. In audio clips, grooves work by adjusting the
clip’s warping behavior, and thus only work on clips with Warp enabled.

14.1 Groove Pool

Once you’ve applied a groove file, you can modify its behavior by adjusting its parameters in the
Groove Pool, which can be opened or closed via drop-down menu entry in the browser view control
or by using the shortcut Ctrl
