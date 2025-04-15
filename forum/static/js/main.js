// Main JavaScript file

document.addEventListener('DOMContentLoaded', () => {
    // Like button for thread
    const threadLikeBtn = document.querySelector('.like-dislike-buttons[data-thread-id] .btn-like');
    const threadDislikeBtn = document.querySelector('.like-dislike-buttons[data-thread-id] .btn-dislike');
    if (threadLikeBtn && threadDislikeBtn) {
        const threadId = threadLikeBtn.parentElement.getAttribute('data-thread-id');

        threadLikeBtn.addEventListener('click', () => {
            fetch(`/thread/${threadId}/like`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.likes !== undefined) {
                        threadLikeBtn.querySelector('.like-count').textContent = data.likes;
                    }
                });
        });

        threadDislikeBtn.addEventListener('click', () => {
            fetch(`/thread/${threadId}/dislike`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.dislikes !== undefined) {
                        threadDislikeBtn.querySelector('.dislike-count').textContent = data.dislikes;
                    }
                });
        });
    }

    // Like and dislike buttons for replies
    document.querySelectorAll('article[data-reply-id]').forEach(replyArticle => {
        const replyId = replyArticle.getAttribute('data-reply-id');
        const likeBtn = replyArticle.querySelector('.btn-like');
        const dislikeBtn = replyArticle.querySelector('.btn-dislike');

        if (likeBtn && dislikeBtn) {
            likeBtn.addEventListener('click', () => {
                fetch(`/reply/${replyId}/like`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.likes !== undefined) {
                            likeBtn.querySelector('.like-count').textContent = data.likes;
                        }
                    });
            });

            dislikeBtn.addEventListener('click', () => {
                fetch(`/reply/${replyId}/dislike`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.dislikes !== undefined) {
                            dislikeBtn.querySelector('.dislike-count').textContent = data.dislikes;
                        }
                    });
            });
        }
    });
});
