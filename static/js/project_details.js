document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing project details page');
    
    const sectionLinks = document.querySelectorAll('.section-link');
    const contentSections = document.querySelectorAll('.content-section');
    const deleteBtn = document.getElementById('deleteProjectBtn');
    const deleteModal = document.getElementById('deleteConfirmModal');
    const closeModalBtn = deleteModal.querySelector('.close-btn');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // Debug info
    console.log(`Found ${sectionLinks.length} section links`);
    console.log(`Found ${contentSections.length} content sections`);

    // Handle section navigation
    sectionLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const sectionId = link.getAttribute('href').substring(1);
            console.log(`Section link clicked: ${sectionId}`);
            
            // Remove active class from all links and sections
            sectionLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link and corresponding section
            link.classList.add('active');
            const section = document.getElementById(sectionId);
            
            if (!section) {
                console.error(`Section not found: ${sectionId}`);
                return;
            }
            
            section.classList.add('active');
            console.log(`Activated section: ${sectionId}`);

            // Load content if it's empty
            const container = section.querySelector('.content-grid');
            if (container && container.children.length === 0) {
                console.log(`Loading content for section: ${sectionId}`);
                await loadSectionContent(sectionId);
            } else if (!container) {
                console.error(`Content grid not found for section: ${sectionId}`);
            } else {
                console.log(`Section ${sectionId} already has content, skipping load`);
            }
        });
    });

    // Delete project functionality
    deleteBtn.addEventListener('click', () => {
        deleteModal.classList.add('active');
    });

    const closeDeleteModal = () => {
        deleteModal.classList.remove('active');
    };

    closeModalBtn.addEventListener('click', closeDeleteModal);
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });

    confirmDeleteBtn.addEventListener('click', async () => {
        const projectId = deleteBtn.dataset.projectId;
        try {
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                window.location.href = '/';
            } else {
                console.error('Failed to delete project');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });

    // Load section content
    async function loadSectionContent(sectionId) {
        const projectId = deleteBtn.dataset.projectId;
        console.log(`Loading content for section ${sectionId} with project ID ${projectId}`);
        
        const container = document.querySelector(`#${sectionId} .content-grid`);
        
        if (!container) {
            console.error(`Container not found for section: ${sectionId}`);
            return;
        }

        container.innerHTML = '<div class="loading">Loading...</div>';

        try {
            console.log(`Fetching ${sectionId} for project ${projectId}`);
            const url = `/api/projects/${projectId}/${sectionId}`;
            console.log(`API URL: ${url}`);
            
            const response = await fetch(url);
            console.log(`API Response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`Received ${data.length} ${sectionId}:`, data);

            if (sectionId === 'videos') {
                displayVideos(container, data);
            } else if (sectionId === 'papers') {
                displayPapers(container, data);
            } else if (sectionId === 'books') {
                console.log('About to display books:', data);
                displayBooks(container, data);
                console.log('Books display function completed');
            } else {
                console.warn(`No display handler for section: ${sectionId}`);
                container.innerHTML = `<div class="empty-state">Content for ${sectionId} not implemented yet</div>`;
            }
        } catch (error) {
            console.error(`Error loading ${sectionId}:`, error);
            container.innerHTML = `<div class="error">Failed to load ${sectionId}. ${error.message}</div>`;
        }
    }

    function formatDuration(duration) {
        if (!duration) return '00:00';
        
        // Convert ISO 8601 duration to readable format
        const match = duration.match(/PT(\d+H)?(\d+M)?(\d+S)?/);
        if (!match) return '00:00';
        
        const hours = (match[1] || '').replace('H', '');
        const minutes = (match[2] || '').replace('M', '') || '0';
        const seconds = (match[3] || '').replace('S', '') || '0';
        
        let result = '';
        if (hours) result += `${hours}:`;
        result += `${minutes.padStart(2, '0')}:`;
        result += seconds.padStart(2, '0');
        return result;
    }

    function formatViews(count) {
        if (!count) return '0 views';
        
        if (count >= 1000000) {
            return `${(count / 1000000).toFixed(1)}M views`;
        } else if (count >= 1000) {
            return `${(count / 1000).toFixed(1)}K views`;
        }
        return `${count} views`;
    }

    function formatRating(rating, count) {
        if (!rating) return '';
        
        const stars = '★'.repeat(Math.floor(rating)) + '☆'.repeat(5 - Math.floor(rating));
        return `${stars} ${rating.toFixed(1)} (${count} reviews)`;
    }

    function displayVideos(container, videos) {
        console.log(`Displaying ${videos ? videos.length : 0} videos`);
        
        if (!videos || videos.length === 0) {
            container.innerHTML = '<div class="empty-state">No videos found</div>';
            return;
        }

        container.innerHTML = '';
        videos.forEach(video => {
            // Create a wrapper div to hold both rating controls and card
            const wrapper = document.createElement('div');
            wrapper.className = 'card-wrapper';
            
            // Create rating controls outside the card
            const ratingControls = document.createElement('div');
            ratingControls.className = 'rating-controls';
            ratingControls.innerHTML = generateRatingButtons(video.relevance_rating);
            wrapper.appendChild(ratingControls);
            
            // Create the card
            const card = document.createElement('div');
            card.className = 'content-card video-card';
            card.dataset.id = video.id;
            card.innerHTML = `
                <div class="relevance-rating">
                    <span class="material-icons">star</span>
                    <span>${video.relevance_rating}/10</span>
                </div>
                <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank" class="video-thumbnail card-thumbnail" data-id="${video.id}">
                    <img src="${video.thumbnail_url}" alt="${video.title}">
                    <span class="duration">${formatDuration(video.duration)}</span>
                </a>
                <div class="card-body">
                    <h4 class="card-title">${video.title}</h4>
                    <div class="card-subtitle">
                        <span class="channel">${video.channel_title}</span>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="card-meta">
                        <span class="meta-item views">${formatViews(video.view_count)}</span>
                        <span class="meta-item click-count">
                            <span class="material-icons">touch_app</span>
                            <span>${video.click_count || 0}</span>
                        </span>
                    </div>
                    <div class="card-actions">
                        <button class="dislike-btn" title="Remove this video">
                            <span class="material-icons">thumb_down</span>
                        </button>
                    </div>
                </div>
            `;
            
            wrapper.appendChild(card);
            container.appendChild(wrapper);
            
            // Add event listeners
            addCardEventListeners(card, 'videos', ratingControls);
        });
    }

    function displayPapers(container, papers) {
        console.log(`Displaying ${papers ? papers.length : 0} papers`);
        
        if (!papers || papers.length === 0) {
            container.innerHTML = '<div class="empty-state">No papers found</div>';
            return;
        }

        container.innerHTML = '';
        papers.forEach(paper => {
            // Create a wrapper div to hold both rating controls and card
            const wrapper = document.createElement('div');
            wrapper.className = 'card-wrapper';
            
            // Create rating controls outside the card
            const ratingControls = document.createElement('div');
            ratingControls.className = 'rating-controls';
            ratingControls.innerHTML = generateRatingButtons(paper.relevance_rating);
            wrapper.appendChild(ratingControls);
            
            // Create the card
            const card = document.createElement('div');
            card.className = 'content-card paper-card';
            card.dataset.id = paper.id;
            card.innerHTML = `
                <div class="relevance-rating">
                    <span class="material-icons">star</span>
                    <span>${paper.relevance_rating}/10</span>
                </div>
                <div class="card-body">
                    <h4 class="card-title">${paper.title}</h4>
                    <div class="card-subtitle">
                        <span class="authors">${paper.authors}</span>
                    </div>
                    <p class="card-text">${paper.abstract || 'No abstract available'}</p>
                </div>
                <div class="card-footer">
                    <div class="card-meta">
                        <span class="meta-item publisher">${paper.publisher || 'Unknown publisher'}</span>
                        <span class="meta-item year">${paper.year || 'Unknown year'}</span>
                        <span class="meta-item click-count">
                            <span class="material-icons">touch_app</span>
                            <span>${paper.click_count || 0}</span>
                        </span>
                    </div>
                    <div class="card-actions">
                        ${paper.pdf_url ? `<a href="${paper.pdf_url}" target="_blank" class="card-link" data-id="${paper.id}">PDF</a>` : ''}
                        ${paper.download_url ? `<a href="${paper.download_url}" target="_blank" class="card-link" data-id="${paper.id}">Download</a>` : ''}
                        <button class="dislike-btn" title="Remove this paper">
                            <span class="material-icons">thumb_down</span>
                        </button>
                    </div>
                </div>
            `;
            
            wrapper.appendChild(card);
            container.appendChild(wrapper);
            
            // Add event listeners
            addCardEventListeners(card, 'papers', ratingControls);
        });
    }

    function displayBooks(container, books) {
        console.log(`Displaying ${books ? books.length : 0} books`);
        
        if (!books || books.length === 0) {
            container.innerHTML = '<div class="empty-state">No books found</div>';
            return;
        }

        container.innerHTML = '';
        books.forEach(book => {
            // Create a wrapper div to hold both rating controls and card
            const wrapper = document.createElement('div');
            wrapper.className = 'card-wrapper';
            
            // Create rating controls outside the card
            const ratingControls = document.createElement('div');
            ratingControls.className = 'rating-controls';
            ratingControls.innerHTML = generateRatingButtons(book.relevance_rating);
            wrapper.appendChild(ratingControls);
            
            // Create the card
            const card = document.createElement('div');
            card.className = 'content-card book-card';
            card.dataset.id = book.id;
            card.innerHTML = `
                <div class="relevance-rating">
                    <span class="material-icons">star</span>
                    <span>${book.relevance_rating}/10</span>
                </div>
                <div class="book-thumbnail card-thumbnail">
                    <img src="${book.thumbnail || '/static/img/book-placeholder.png'}" alt="${book.title}">
                </div>
                <div class="card-body">
                    <h4 class="card-title">${book.title}</h4>
                    <div class="card-subtitle">
                        <span class="authors">${book.authors || 'Unknown author'}</span>
                    </div>
                    <p class="card-text">${book.description || 'No description available'}</p>
                </div>
                <div class="card-footer">
                    <div class="card-meta">
                        <span class="meta-item publisher">${book.publisher || 'Unknown publisher'}</span>
                        <span class="meta-item published-date">${book.published_date || ''}</span>
                        <span class="meta-item click-count">
                            <span class="material-icons">touch_app</span>
                            <span>${book.click_count || 0}</span>
                        </span>
                    </div>
                    <div class="card-actions">
                        ${book.preview_link ? `<a href="${book.preview_link}" target="_blank" class="card-link preview-link" data-id="${book.id}">Preview</a>` : ''}
                        ${book.buy_link ? `<a href="${book.buy_link}" target="_blank" class="card-link buy-link" data-id="${book.id}">Buy</a>` : ''}
                        <button class="dislike-btn" title="Remove this book">
                            <span class="material-icons">thumb_down</span>
                        </button>
                    </div>
                </div>
            `;
            
            wrapper.appendChild(card);
            container.appendChild(wrapper);
            
            // Add event listeners
            addCardEventListeners(card, 'books', ratingControls);
        });
    }

    // Generate rating buttons (1-10)
    function generateRatingButtons(currentRating) {
        let buttons = '';
        for (let i = 1; i <= 10; i++) {
            const isActive = i === currentRating ? 'active' : '';
            buttons += `<button class="rating-btn ${isActive}" data-rating="${i}">
                ${i}
            </button>`;
        }
        return buttons;
    }

    // Add event listeners to card elements
    function addCardEventListeners(card, contentType, ratingControls) {
        const id = card.dataset.id;
        
        // Track clicks on content links
        const links = card.querySelectorAll('a[data-id]');
        links.forEach(link => {
            link.addEventListener('click', async (e) => {
                try {
                    const response = await fetch(`/api/${contentType}/${id}/click`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        const clickCountEl = card.querySelector('.click-count span:last-child');
                        if (clickCountEl) {
                            clickCountEl.textContent = data.click_count;
                        }
                    }
                } catch (error) {
                    console.error(`Error tracking click for ${contentType} ${id}:`, error);
                }
            });
        });
        
        // Handle relevance rating
        const ratingButtons = ratingControls.querySelectorAll('.rating-btn');
        ratingButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const rating = parseInt(button.dataset.rating);
                
                try {
                    const response = await fetch(`/api/${contentType}/${id}/rate`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ rating })
                    });
                    
                    if (response.ok) {
                        // Update UI
                        const ratingEl = card.querySelector('.relevance-rating span:last-child');
                        if (ratingEl) {
                            ratingEl.textContent = `${rating}/10`;
                        }
                        
                        // Update active button
                        ratingButtons.forEach(btn => btn.classList.remove('active'));
                        button.classList.add('active');
                    }
                } catch (error) {
                    console.error(`Error rating ${contentType} ${id}:`, error);
                }
            });
        });
        
        // Handle dislike button
        const dislikeBtn = card.querySelector('.dislike-btn');
        if (dislikeBtn) {
            dislikeBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const response = await fetch(`/api/${contentType}/${id}/hide`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        // Animate and remove card
                        card.classList.add('removing');
                        setTimeout(() => {
                            card.remove();
                        }, 500);
                    }
                } catch (error) {
                    console.error(`Error hiding ${contentType} ${id}:`, error);
                }
            });
        }
    }

    // Load initial section content
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
        console.log(`Initial active section: ${activeSection.id}`);
        loadSectionContent(activeSection.id);
    } else {
        console.warn('No active section found on page load');
    }
    
    // Automatically activate books section for testing
    setTimeout(() => {
        console.log('Automatically activating books section for testing');
        const booksLink = document.querySelector('a[href="#books"]');
        if (booksLink) {
            console.log('Books link found, clicking it');
            booksLink.click();
        } else {
            console.error('Books link not found');
        }
    }, 2000);
});
