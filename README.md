# BaSc Collaboration Webpage


In order to test locally, make sure to have the `extended` version of [Hugo installed](https://gohugo.io/installation/).
The site works with Hugo version 0.161.1.  Precompiled Hugo binaries are available [here](github.com/gohugoio/hugo/releases/tag/v0.151.0) or can be installed with `brew install hugo`.
Installation requires downloading the correct binary for your system's architecture and decompressing it into a folder in your path.
Then,
```
git clone --recursive https://github.com/BASC-Collaboration/BASC-Collaboration.github.io
cd BASC-Collaboration.github.io
git submodule update --remote --recursive
hugo serve
```
This should launch a webpage locally that you can view at the site:
```
http://localhost:1313/
```
or whichever address the prompt from the terminal tells you.  If this does not work, then stop serving the site, and do
```
bash themes/hugo-texademic/scripts/add_npm_modules.sh
```
and then try serving the site again.  You may also have to install `Dart sass`, with instructions [here](https://gohugo.io/functions/css/sass/#dart-sass).  If this still does not work, contact André.

After you have a working site, you can add new content by making a new branch
```
git checkout -b <branch_name>
```
To make yourself a new member page, you can type
```
hugo new members/<CATEGORY>/<YOUR_NAME>.md
```
where `CATEGORY = [seniors, postdocs, gradstudents, undergrads, former ]`.  This will create a template file that you can edit, and then add and commit.  Make sure to add your image to `assets/images/portraits` folder, and then list `images/portraits/<YOUR_IMAGE>.{jpg,png}` in the `portrait` key.

Add additional content, such as news items.  Then, make sure it works locally, add the new files
```
git add <files you added/modified>
git commit -m "some useful message"
git push
```
and then issue a pull request to the `main` branch and assign @walkloud
