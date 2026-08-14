# OnBxrd Landing Assets

The public landing page is complete without image files. Its media areas render as intentional visual placeholders until local assets are supplied, so the page never requests a missing image or fetches a remote one.

Add approved, rights-cleared landing images to the folder that matches their use:

| Folder | Intended image set | Suggested names |
| --- | --- | --- |
| `hero/` | Main opening-stage images | `hero-01.jpg`, `hero-02.jpg` |
| `features/welcome/` | Welcome feature images | `welcome-01.jpg`, `welcome-02.jpg` |
| `features/help/` | Guidance feature images | `help-01.jpg`, `help-02.jpg` |
| `features/work/` | Role-work feature images | `work-01.jpg`, `work-02.jpg` |
| `workflows/` | Guidance-to-request journey images | `workflow-01.jpg`, `workflow-02.jpg` |
| `stories/` | Closing or building-life images | `story-01.jpg`, `story-02.jpg` |

Every media area automatically reads and rotates through the image files in its own folder. No filename manifest is required: add any `.avif`, `.gif`, `.jpeg`, `.jpg`, `.png`, or `.webp` file and restart `npm run dev` so Next.js refreshes the server-rendered file list. The page keeps only a working image if another file fails to load.

For backward compatibility, a flat `features/` folder still works when filenames begin with `welcome-`, `help-`, or `work-`; dedicated subfolders avoid accidental reuse. Keep each image collection independent, do not reuse a feature image as proof of a product claim, and do not introduce remote image URLs. The named `data-asset-slot` values remain stable in `app/page.tsx`.
