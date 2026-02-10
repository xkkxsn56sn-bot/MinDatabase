# MinDatabase Docs Site

This folder is the GitHub Pages source.

## Local preview

From this folder:

```bash
bundle install
bundle exec jekyll serve --livereload
```

Then open http://127.0.0.1:4000/MinDatabase/.

## If the server fails

- Update bundler: `gem install bundler`
- Retry: `bundle update --bundler`

## Deploy

Push to `main`. GitHub Pages will build from the `docs/` folder.
