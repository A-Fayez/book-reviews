# book-reviews

A simple web-based app using Flask allows different users to:

- Register and login.
- Search and submit reviews on their favourite books.

# API

Make a GET request to `/api/<isbn>` to get a JSON response containing
book's title, author, publication year, ISBN number, review count, and average score.

```javascript
// JSON sample
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}
```

## Deployment

The app is deployed to a self-hosted kubernetes cluster on AWS EC2, which is provisioned using ansible. All source files are found in the [deploy](deploy) dir.
