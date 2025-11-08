---
id: 06
title: "(Mac)."
chapter: 06
---
# 6 (Mac).

Option

Alt

The Groove Pool View Control.

You can also double-click grooves in the browser to load them directly to the Groove Pool before
applying them to a clip. The Groove Pool contains all grooves that have been loaded in this way or
that are being used in clips. “Inactive“ grooves (those that are not being used by a clip) appear with
their parameters grayed out.

The Groove Pool.

14.1.1 Adjusting Groove Parameters

Grooves in the Groove Pool appear in a list, and offer a variety of parameters that can be modified in
real time to adjust the behavior of any clips that are using them. You can also save and hot-swap
grooves via the buttons next to the Groove’s name.

The Groove Pool’s controls work as follows:

•

•

•
•

•

Base — The Base chooser determines the timing resolution against which the notes in the groove
will be measured. A 1/4 Base, for example, means that the positions of the notes in the groove
file are compared to the nearest quarter note, and all notes in any clips that are assigned to that
groove will be moved proportionally towards the positions of the groove notes. At a base of
1/8th, the groove’s notes are measured from their nearest eighth note. Notes in the groove that
fall exactly on the grid aren’t moved at all, so the corresponding notes in your clips will also not
be moved.
Quantize — adjusts the amount of “straight“ quantization that is applied before the groove is
applied. At 100%, the notes in your clips will be snapped to the nearest note values, as
selected in the Base chooser. At 0%, the notes in clips will not be moved from their original
positions before the groove is applied.
Timing — adjusts how much the groove pattern will affect any clips which are using it.
Random — adjusts how much random timing fluctuation will be applied to clips using the
selected groove. At low levels, this can be useful for adding subtle “humanization“ to highly
quantized, electronic loops. Note that Random applies differing randomization to every voice
in your clip, so notes that originally occurred together will now be randomly offset both from the
grid and from each other.
Velocity — adjusts how much the velocity of the notes in clips will be affected by the velocity
information stored in the groove file. Note that this slider goes from -100 to +100. At negative

•

values, the effect of the groove’s velocity will be reversed; loud notes will play quietly and vice
versa.
Global Amount — this parameter scales the overall intensity of Timing, Random and Velocity for
all of the available groove files. At 100%, the parameters will be applied at their assigned
values. Note that the Amount slider goes up to 130%, which allows for even more exaggerated
groove effects. If grooves are applied to clips in your Set, the Global Amount slider will also
appear in Live’s Control Bar.

The Global Groove Amount Slider in the Control Bar

14.1.2 Committing Grooves

The Commit Groove Button.

Pressing the Commit button above the Clip Groove chooser “writes“ your groove parameters to the
clip. For MIDI clips, this moves the notes accordingly. For audio clips, this creates Warp Markers at the
appropriate positions in the clip.

After pressing Commit, the clip’s Groove chooser selection is automatically set to None.

14.2 Editing Grooves

The effect that groove files have on your clips is a combination of two factors: the parameter settings
made in the Groove Pool and the positions of the notes in the groove files themselves. To edit the
contents of groove files directly, drag and drop them from the browser or Groove Pool into a MIDI
track. This will create a new MIDI clip, which you can then edit, as you would with any other MIDI
clip. You can then convert the edited clip back into a groove, via the process below.

14.2.1 Extracting Grooves

The timing and volume information from any audio or MIDI clip can be extracted to create a new
groove. You can do this by dragging the clip to the Groove Pool or via the Extract Groove command
in the clip’s context menu.

Extract Grooves From Audio or MIDI Clips.

Grooves created by extracting will only consider the material in the playing portion of the clip.

14.3 Groove Tips

This section presents some tips for getting the most out of grooves.

14.3.1 Grooving a Single Voice

Drummers will often use variations in the timing of particular instruments in order to create a
convincing beat. For example, playing hi-hats in time but placing snare hits slightly behind the beat is
a good way of creating a laid-back feel. But because groove files apply to an entire clip at once, this
kind of subtlety can be difficult to achieve with a single clip. Provided your clip uses a Drum or
Instrument Rack, one solution can be to extract the chain containing the voice that you want to
independently groove. In this example, we’d extract the snare chain, creating a new clip and track
that contained only the snare notes. Then we could apply a different groove to this new clip.

14.3.2 Non-Destructive Quantization

Grooves can be used to apply real-time, non-destructive quantization to clips. To do this, simply set
the groove’s Timing, Random and Velocity amounts to 0% and adjust its Quantize and Base
parameters to taste. With only Quantize applied, the actual content of the groove is ignored, so this
technique works the same regardless of which Groove file you use.

14.3.3 Creating Texture With Randomization

You can use a groove’s Random parameter to create realistic doublings. This can be particularly useful
when creating string textures from single voices. To do this, first duplicate the track containing the clip
that you want to “thicken.“ Then apply a groove to one of the clips and turn up its Random parameter.
When you play the two clips together, each note will be slightly (and randomly) out of sync with its
counterpart on the other track.

15. Using Tuning Systems

By default Live uses 12TET tuning, this means note pitches are divided equally into twelve parts per
octave. However, there are numerous ways that pitches can be distributed across an octave or
pseudo-octave (where notes are repeated at a different interval than an octave), and tuning systems
can be used to specify these variations.

Live 12 supports Scala files, which you can load into a Live Set to use a custom tuning for notes.

The Core Library also comes with a set of tuning systems, which can be found in the Tunings label of
the browser. Tuning files from the Core Library use an Ableton-specific extension to the SCL (Scala)
file format called ASCL.

The Tunings Label in the Browser.

When hovering over or selecting tuning systems in the browser, a short description of the tuning,
including the number of notes per octave, is shown in the Info View. This description is also shown
when hovering over the name of a loaded tuning system.

A Tuning System Description in the Info View.

You can add your own .scl or .ascl files to any folder in Live’s Places so that they show up in the
Tunings label of the browser under the User tag.

User-saved Tunings in the Browser.

All of Live’s built-in instruments are supported for use with tuning systems, as well as MPE-enabled
plug-ins or external Max for Live instruments, provided that their pitch bend range is set to 48
semitones.

Note that instruments that are not MPE-enabled or use different pitch bend ranges are likely to play
out of tune.

15.1 Loading a Tuning System

To load a tuning system into a Set, you can double-click on a tuning file in the browser, or select the
file and press Enter . These methods will automatically open the Tuning section of the browser, which
is hidden by default.

The Tuning section in the Browser.

You can also open the Tuning section using the browser’s view control menu.

The Browser View Control Menu.

External ASCL or SCL files on your computer can be dragged and dropped into the Tuning section as
well. As long as the file is loaded in the Tuning section, the tuning will be saved with the Live Set.

When a tuning system is added to a Live Set, the notes in the piano roll no longer represent standard
MIDI notes, but instead show the corresponding notes of the tuning.

Updated Notes in the MIDI Note Editor.

You can hover over a note in the piano roll to see useful information, such as the note’s pitch and
frequency, in the Status Bar. The specified pitch is produced when a note is played in the piano roll or
via a keyboard.

Hover Over a Note in the Piano Roll for Pitch Information.

By default, if a tuning system is removed or changed to a different tuning, the position of existing notes
in the piano roll is not changed, but the pitches shown in the note ruler are updated to match the new
tuning. This means the original notes may not produce the same pitch.

The “Retune Set On Loading Tuning Systems” entry in the Options menu can be enabled so that when
a tuning system is loaded or changed, the notes will closely match the pitches of the original notes,
ensuring that a melody sounds as close to the original as possible. You will see a dialog appear to
confirm this process when loading a tuning system.

Existing MIDI Clips May Be Modified when Loading a Tuning System.

When automatic note retuning is enabled, removing or switching between tuning systems can cause
original notes to be changed or lost. This can happen when two notes which overlap in time and
originally had different pitches both get mapped to the same pitch in the new tuning system, as that
new pitch is closest to both original pitches. In that case, one of the notes may be deleted or
shortened.

Note that the Scale Mode choosers in Clip View and the Control Bar are no longer visible when a
tuning system is loaded.

15.2 The Tuning Section

Various pitch settings for a tuning system are accessible via the Tuning section.

The Tuning Section Expanded.

You can toggle the triangle next to the name of the tuning file to expand the section and access
additional settings for the lowest and highest notes for the reference pitch.

•
•
•
•

•

•

Tuning displays the name of the tuning system.
Octave sets the octave of the note used for the reference pitch.
Note sets the note in the octave used for the reference pitch.
Ref. Pitch/Freq sets the frequency of the reference pitch. The pitch of all notes in the Set can be
raised or lowered by changing the frequency.
Lowest Note sets what the lowest note plays by assigning it to an octave and pitch class.
Changing the lowest note also affects the highest note, preserving the number of notes in
between.
Highest Note sets what the highest note plays; changing the highest note will also update the
lowest note.

Note that the reference pitch is only audibly affected by the Ref. Pitch/Freq value. Changing the
Octave or Note values will update the frequency displayed in the Ref. Pitch/Freq slider to match the
newly specified notes, however, no audible change is produced until the reference pitch frequency
value itself is adjusted. This is to prevent any sudden pitch changes when setting the Octave or Note
values.

The floppy disk button to the right of the reference pitch frequency can be used to save the currently
loaded tuning as an .ascl file to the Tunings label in the browser.

Pressing the arrow button next to the Save Tuning System button opens a link to Ableton’s Tuning
website that contains more information about the loaded tuning system, as well as an interactive editor
for trying out variations of the associated pitches. You can also export any custom tuning systems you
create there. Note that not all tuning systems have external webpages, and the arrow button will be
greyed out if no relevant link is available.

You can select a file in the Tuning section and press the Delete key to remove it and return to 12TET
tuning.

15.3 MIDI Track Options for Tuning Systems

You will see a few tuning-specific options appear in the I/O section of MIDI tracks when a tuning
system is loaded that let you customize your track and controller setups.

15.3.1 Bypass Tuning

The Bypass Tuning toggle can be used to ignore a tuning system for a specific MIDI track.

The Bypass Tuning Toggle.

When enabled, the MIDI Note Editor will display 12TET tuning notes in the piano roll for any clips in
that track.

Note that MIDI tracks containing Drum Racks automatically bypass any loaded tuning file.

15.3.2 MIDI Controller Layouts

As notes in a tuning system can differ from 12TET layouts, the Track Tuning MIDI Controller Layout
settings allow you to specify which notes a controller can be mapped to, as well as create a custom
layout if needed. This is useful for re-aligning the layout of an external keyboard to match the piano
roll, if the layout differs when using certain tunings.

The Track Tuning MIDI Controller Layout Options.

•
•
•
•
•

All Keys maps notes in the tuning system to all keys on the controller.
Black Keys Only maps notes to the black keys only. This layout is centered around C#3.
White Keys Only maps notes to the white keys only. This layout is centered around C3.
Closest in Pitch to Keyboard maps notes to the closest pitch on the keys.
Custom Controller Layout lets you define a specific layout for the controller.

When Custom Controller Layout is selected in the chooser, you can press the … button to the right to
access the Configure MIDI Layout dialog and adjust the layout settings.

The Configure MIDI Layout Dialog.

Custom controller layouts will be saved and recalled with the Live Set.

15.4 Learn More About Tuning Systems

You can visit Ableton’s Tuning website to read more about Live’s built-in tuning systems, as well as
create and export your own custom tunings using interactive widgets.

Using the ASCL format, you can also create and import your own tuning systems for Live by following
the designated specifications.

16. Launching Clips

The Live Session View is set apart by the fact that it gives you, the musician, a spontaneous
environment that encourages performance and improvisation. An important part of how you take
advantage of the Session View lies within how you configure your various Session View clips. This
chapter explains the group of settings used to define how each Session View clip behaves when
triggered, or “launched.“

16.1 The Launch Controls

Remember that clips in the Session View are launched by their Clip Launch buttons or remote control.
Clip launch settings can be found in the corresponding clip panel. The clip launch settings only apply
to Session View clips, as Arrangement View clips are not launched but played according to their
positions in the Arrangement.

To view the clip launch settings, open the Clip View of a Session View clip by double-clicking the clip,
then click on the clip tab/panel with the Clip Launch button icon.

The Clip Launch Settings in a Clip Tab.

Note that you can edit the launch settings of more than one clip at the same time by first selecting the
clips and then opening the Clip View.

16.2 Launch Modes

The Clip Launch Chooser.

The Launch Mode chooser offers a number of options for how clips behave with respect to mouse
clicks, computer keyboard actions or MIDI notes:

•
•
•
•

Trigger: down starts the clip; up is ignored.
Gate: down starts the clip; up stops the clip.
Toggle: down starts the clip; up is ignored. The clip will stop on the next down.
Repeat: As long as the mouse switch/key is held, the clip is triggered repeatedly at the clip
quantization rate.

16.3 Legato Mode

The Legato Mode Switch.

Suppose you have gathered, in one track, a number of looping clips, and you now want to toggle
among them without losing the sync. For this you could use a large quantization setting (one bar or
greater), however, this might limit your musical expression.

Another option, which works even with quantization turned off, is to engage Legato Mode for the
respective clips. When a clip in Legato Mode is launched, it takes over the play position from
whatever clip was played in that track before. Hence, you can toggle clips at any moment and rate
without ever losing the sync.

Legato Mode is very useful for creating breaks, as you can momentarily play alternative loops and
jump back to what was playing in the track before.

Unless all the clips involved play the same sample (differing by clip settings only), you might hear
dropouts when launching clips in Legato Mode. This happens because you are unexpectedly jumping
to a point in the sample that Live has had no chance to preload from disk in advance. You can remedy
this situation by engaging Clip RAM Mode for the clips in question.

16.4 Clip Launch Quantization

The Clip Quantization Chooser.

The Clip Quantization chooser lets you adjust an onset timing correction for clip triggering. To disable
clip quantization, choose “None.“

To use the Control Bar’s Global Quantization setting, choose “Global.“ Global quantization can be
quickly changed using the Ctrl
0 (Mac) shortcuts.
