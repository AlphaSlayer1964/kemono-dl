# kemono-dl
A downloader tool for kemono and coomer websties.

## How to use
1. **Install Python 3**  

2. **Download the latest release**  
   Get the source code for the [latest version](https://github.com/AplhaSlayer1964/kemono-dl/releases/latest) and extract it.

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4.  **Run Python Module**  
    ```bash
    python -m kemono_dl "https://kemono.cr/SERVICE/user/CREATOR_ID" 
    python -m kemono_dl "https://coomer.st/SERVICE/user/CREATOR_ID/post/POST_ID"
    ```

# Command Line Options

| Option                       | Description                                                                                                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--path PATH`                | Set the base path for downloads.                                                                                                                                                       |
| `--output OUTPUT_TEMPLATE`   | Set the file name pattern for attachments. See [Output Template Variables](https://github.com/AlphaSlayer1964/kemono-dl?tab=readme-ov-file#output-template-variables) for more detail. |
| `--batch-file FILE`          | Loads urls from file. One url per line.                                                                                                                                                |
| `--coomer-cookies FILE`      | Provide a cookies file for Coomer. Required for `--favorite-creators-coomer`.                                                                                                          |
| `--kemono-cookies FILE`      | Provide a cookies file for Kemono. Required for `--favorite-creators-kemono`.                                                                                                          |
| `--favorite-creators-coomer` | Download all favorite creators from Coomer.                                                                                                                                            |
| `--favorite-creators-kemono` | Download all favorite creators from Kemono.                                                                                                                                            |

## Output Template Variables

The output template is simply a [Python formatted string](https://docs.python.org/3/library/string.html#formatstrings).  
You can use any valid Python string formatting syntax, including custom text, slashes, and nested variables. For example:  
`"{creator_name}/{post_id}_{filename}"` will organize downloads into folders by creator name.

These placeholders can be used in the `--output` pattern:

| Variable             | Description                                                                                                                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{service}`          | Service Name.                                                                                                                                                                                                    |
| `{creator_id}`       | Creator's ID                                                                                                                                                                                                     |
| `{creator_name}`     | Creator's name.                                                                                                                                                                                                  |
| `{post_id}`          | Post ID.                                                                                                                                                                                                         |
| `{post_title}`       | Post title.                                                                                                                                                                                                      |
| `{server_filename}`  | Server file name (with extension).                                                                                                                                                                               |
| `{server_file_name}` | Server file name (without extension).                                                                                                                                                                            |
| `{server_file_ext}`  | Server file extension (without the ".") (May be different from `{file_ext}`).                                                                                                                                    |
| `{filename}`         | Original file name (with extension). **(\*5)**                                                                                                                                                                   |
| `{file_name}`        | Original file name (without extension).                                                                                                                                                                          |
| `{file_ext}`         | Original file extension (without the ".") (May be different from `{server_file_ext}`).                                                                                                                           |
| `{sha256}`           | SHA-256 hash of the file generated by Kemono/Coomer.                                                                                                                                                             |
| `{added}`            | DateTime the post was added to kemono/coomer. Use `{added:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3, \*4)**   |
| `{published}`        | DateTime the post was published to service. Use `{published:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3, \*4)** |
| `{edited}`           | DateTime the post was edited by kemono/coomer. Use `{edited:FORMAT}` to format. See [format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **(\*1, \*2, \*3, \*4)** |

> **\*1** If there is an error parsinf `{added}`, `{published}`, or `{edited}` it will default to `January 1, 0001`. This includes if any of those values are `Null` for the post.  

> **\*2** The Fanbox service always has `{added}` as `Null` so it will always return `January 1, 0001`.  

> **\*3** DateTime variables like `{added}` include colons (`:`) by default, which are invalid in Windows file paths. Use `{added:FORMAT}` with a safe format like `%Y-%m-%d %H-%M-%S`.  

> **\*4** In Windows batch files, you must escape `%` with `%%`.  

> **\*5** Be mindful that `{filename}` is not guaranteed to be unique. It is recomended to use `{server_filename}` or `{sha256}` to guaranteed uniqueness.  

### Output Template Examples
```bash
python -m kemono_dl --output "{service}/{creator_id}/{post_id}/{filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890/attachment.png

python -m kemono_dl --output "{service}/{creator_id}/{post_id}/{server_filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890/wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4.png 
# wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4 is the SHA-256 hash of the file that kemono/coomer generated

python -m kemono_dl --output "{service}/{creator_id}/{post_id}_{file_name}_{sha256}.{ext}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/67890_attachment_wm54swsglbfs4583qzp7u880tmglvdqzeg6vqni12s6ywfsk3l8afp5ycfwo2hw4.png

python -m kemono_dl --output "{service}/{creator_id}/[{published:%Y-%m-%d %H-%M-%S}]_{post_id}/{filename}" "https://kemono.cr/patreon/user/12345/post/67890"
patreon/12345/[2025-08-13 00-00-00]_67890/attachment.png # The post was published on August 13, 2025 at 12:00:00 AM
```