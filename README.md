# kemono-dl
A downloader tool for kemono and coomer websties.
> ⚠️ Starting from version `2025.08.13`, kemonod-dl is no longer fully backward compatible with earlier releases. If you prefer the default download template used in older versions, you can manually specify it using:
> ```bash
> --output "{service}/{creator_name} [{creator_id}]/[{published:%Y%m%d}] [{post_id}] {post_title}/{index}_{filename}"
> ```
> Keep in mind that while this template closely mirrors the previous behavior, older versions included logic to truncate file paths and names exceeding 255 characters. This new version does not replicate that trimming exactly, but the template should still work correctly in most cases.
 
## Installation
1. **Install Python**  
   Make sure Python 3.11 or later is installed and available in your system PATH.

2. **Download the latest release**  
   Get the source code for the [latest version](https://github.com/AplhaSlayer1964/kemono-dl/releases/latest) and extract it.

3. **Install with pip**  
   Open a terminal and **navigate to the root folder of the extracted project** (where `pyproject.toml` is located). Then run:
   ```bash
   pip install .
   ```

4.  **Run kemono-dl**  
    ```bash
    kemono-dl --version
    kemono-dl "https://kemono.cr/SERVICE/user/CREATOR_ID" 
    kemono-dl "https://coomer.st/SERVICE/user/CREATOR_ID/post/POST_ID"
    ```

> **\*** To update, repeat steps 2 and 3 using the latest release.

# Command Line Options

| Option                             | Description                                                                                                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--version`                        | Prints the version then quits.                                                                                                                                |
| `--path PATH`                      | Set the base path for downloads.                                                                                                                              |
| `--output [Type:]TEMPLATE(s)`      | Set the output template file pattern. See [Output Template](https://github.com/AlphaSlayer1964/kemono-dl?tab=readme-ov-file#output-template) for more detail. |
| `--batch-file FILE`                | Loads urls from file. One url per line.                                                                                                                       |
| `--cookies FILEs`                  | Provide a cookies file(s) for Kemono/Coomer. Required for `--favorite-creators-coomer` and `--favorite-creators-kemono`.                                      |
| `--favorite-creators-coomer`       | Download all favorite creators from Coomer.                                                                                                                   |
| `--favorite-creators-kemono`       | Download all favorite creators from Kemono.                                                                                                                   |
| `--coomer-login USERNAME PASSWORD` | Username and password for Coomer.                                                                                                                             |
| `--kemono-login USERNAME PASSWORD` | Username and password for Kemono.                                                                                                                             |
| `--restrict-name`                  | Restrict output file to ASCII characters.                                                                                                                     |
| `--custom-template-variables FILE` | Path to a json file with your custom template variables                                                                                                       |
| `--date [Type:]DATE`               | Download only posts published on this date. Format 'YYYYMMDD' **(\*1)**                                                                                       |
| `--datebefore [Type:]DATE`         | Download only posts published on or before this date. Format 'YYYYMMDD' **(\*1)**                                                                             |
| `--dateafter [Type:]DATE`          | Download only posts published on or after this date. Format 'YYYYMMDD' **(\*1)**                                                                              |
| `--skip-extensions EXTs`           | A comma seperated list of file extensions to skip (Do not include the period) (Checks the extention of the filename not the server filename).                 |
| `--skip-attachments`               | Skip downloading post attachments.                                                                                                                            |
| `--write-content`                  | Write the post content to a file.                                                                                                                             |
| `--no-tmp`                         | Do not use `.tmp` files. Write directly into the output file.                                                                                                 |

> **\*1** You can apply date filters to different types. The available options are `"added:YYYYMMDD"`, `"edited:YYYYMMDD"`, and `"published:YYYYMMDD"`. If no type is specified, the published date is used by default.

## Output Template

### Output Template Type

Output template types let you define custom file path formats for different categories of output. By default, all types use the following template: `"{service}/{creator_id}/{post_id}/{filename}"`.
If no specific type is provided, this passed template will be applied for all output types.  

| Type           | Description                                      |
| -------------- | ------------------------------------------------ |
| `"attachment"` | The output template for saving post attachments. |
| `"content"`    | The output template for saving post content.     |

#### Output Template Type Examples
```bash
kemono-dl --output "{service}/{creator_id}/{post_id}/{index}_{filename}" --output "content:{service}/{creator_id}/{post_id}/{filename}" "https://kemono.cr/patreon/user/12345/post/67890" 
patreon/12345/67890/0_attachment.png
patreon/12345/67890/1_attachment.png
patreon/12345/67890/content.html
```

### Output Template Variables

| Variable              | Description                                                                                                                                                                                                 |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{service}`           | Service Name.                                                                                                                                                                                               |
| `{creator_id}`        | Creator's ID                                                                                                                                                                                                |
| `{creator_name}`      | Creator's name.                                                                                                                                                                                             |
| `{post_id}`           | Post ID.                                                                                                                                                                                                    |
| `{post_title}`        | Post title.                                                                                                                                                                                                 |
| `{server_filename}`   | Server file name (with extension).                                                                                                                                                                          |
| `{server_file_name}`  | Server file name (without extension) (equivalent to `{sha256}`).                                                                                                                                            |
| `{server_file_ext}`   | Server file extension (without the ".") (May be different from `{file_ext}`).                                                                                                                               |
| `{filename}`          | Original file name (with extension). **(\*4)**                                                                                                                                                              |
| `{file_name}`         | Original file name (without extension).                                                                                                                                                                     |
| `{file_ext}`          | Original file extension (without the ".") (May be different from `{server_file_ext}`).                                                                                                                      |
| `{sha256}`            | SHA-256 hash of the file generated by Kemono/Coomer.                                                                                                                                                        |
| `{added}`             | DateTime the post was added to kemono/coomer. Use `{added:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3)**   |
| `{published}`         | DateTime the post was published to service. Use `{published:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3)** |
| `{edited}`            | DateTime the post was edited by kemono/coomer. Use `{edited:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3)** |
| `{index}`             | The index order of the posts file and attachments. (Starts at 0) **(\*5)**                                                                                                                                  |
| `{attachments_count}` | The total number of post attchments (Includes post file).                                                                                                                                                   |

> **\*1** If there is an error parsinf `{added}`, `{published}`, or `{edited}` it will default to `January 1, 0001`. This includes if any of those values are `Null` for the post.  

> **\*2** The Fanbox service always has `{added}` as `Null` so it will always return `January 1, 0001`.  

> **\*3** In Windows batch files, you must escape `%` with `%%`.  

> **\*4** Be mindful that `{filename}` is not guaranteed to be unique. It is recomended to use `{server_filename}` or `{sha256}` to guaranteed uniqueness.  

> **\*5** If a Post has a Post `File` it will be index 0 followed by the other `Attachments`.

#### Output Template Examples
```bash
kemono-dl --output "{service}/{creator_id}/{post_id}/{filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890/attachment.png

kemono-dl --output "{service}/{creator_id}/{post_id}/{server_filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890/wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4.png 
# wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4 is the SHA-256 hash of the file that kemono/coomer generated

kemono-dl --output "{service}/{creator_id}/{post_id}_{file_name}_{sha256}.{ext}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890_attachment_wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4.png

kemono-dl --output "{service}/{creator_id}/[{published:%Y-%m-%d %H-%M-%S}]_{post_id}/{filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/[2025-08-13 00-00-00]_67890/attachment.png # The post was published on August 13, 2025 at 12:00:00 AM
```

#### Custom Template Variables

You can define your own template variables in a JSON file, and they will be evaluated as Python expressions.
Custom variables can also reference built-in template variables using `{...}` syntax.

```json
{
   "titleTrunc": "'{post_title}'[:50]",
   "titleNoDogs": "'{post_title}'.replace('dog', 'cat')",
   "indexPlusOne": "{index} + 1",
   "indexPlusOneZfilled": "str({index} + 1).zfill(len(str({attachments_count})))"
}
```
In your output template, simply use the variables like the default ones (ie `{titleTrunc}`) to insert their evaluated values.

> Note: You cannot overwrite the default template variables. Custom variables must use unique names that don't conflict with the built-in ones.