# Landing image folders

Add `.jpg` screenshots to the matching folder. OnBxrd discovers them at build
time, so **do not edit filenames or components** after adding images. Filenames
are sorted naturally (`1.jpg`, `2.jpg`, `10.jpg`) and image selection changes
subtly only while that landing chapter is active.

Each folder has a deliberately different visual treatment. Supply fewer files
than the limit when a simpler composition tells the story better; one image and
no images are both supported without a broken layout.

| Folder | Maximum JPGs used | How the images appear | Best screenshots |
| --- | ---: | --- | --- |
| `onboarding/` | 2 | One large welcome/progress view with one small supporting card | Onboarding checklist, resident profile, building starter content |
| `benefits/` | 4 | Uneven, scattered collage with varied crop sizes | Amenity and benefit discovery screens with clear visual variety |
| `assistant/` | 2 | Small source or attachment previews beside the Hommie chat | Assistant answer, cited handbook, or proposed ticket review |
| `tickets/` | 3 | Evidence cards along a support-status timeline | Ticket creation, a ticket conversation, and a resolved/updated state |
| `announcements/` | 4 | Overlapping noticeboard cards, not a uniform gallery | Announcement list, an announcement detail, notification status |
| `operations/` | 3 | One dominant management screen plus up to two floating scoped panels | Queue/dashboard, resident scope, knowledge, handoff, units, or notification operations |

Guidelines:

- Use only `.jpg` files. Extra files beyond the table limit are safely ignored
  by that scene rather than making it crowded.
- Use real product screenshots where possible. Avoid text that includes real
  resident information or credentials.
- Keep full-screen screenshots reasonably clean; the landing preserves their
  aspect ratio. Decorative thumbnail roles may crop, but important UI text is
  never intentionally cropped.
- The default landing language is Vietnamese and the default theme is night
  mode, so screenshots that work in dark mode are especially useful.
