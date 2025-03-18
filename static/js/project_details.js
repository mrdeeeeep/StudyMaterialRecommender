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
            const card = document.createElement('div');
            card.className = 'video-card';
            card.innerHTML = `
                <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank" class="video-thumbnail">
                    <img src="${video.thumbnail_url}" alt="${video.title}">
                    <span class="duration">${formatDuration(video.duration)}</span>
                </a>
                <div class="video-info">
                    <h4 class="video-title">${video.title}</h4>
                    <div class="video-meta">
                        <span class="channel">${video.channel_title}</span>
                        <span class="views">${formatViews(video.view_count)}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
        
        console.log('Videos displayed successfully');
    }

    function displayPapers(container, papers) {
        console.log(`Displaying ${papers ? papers.length : 0} papers`);
        
        if (!papers || papers.length === 0) {
            container.innerHTML = '<div class="empty-state">No academic papers found</div>';
            return;
        }

        console.log('Displaying papers:', papers);
        container.innerHTML = '';
        
        papers.forEach((paper, index) => {
            console.log(`Processing paper ${index + 1}:`, paper);
            
            const card = document.createElement('div');
            card.className = 'paper-card';
            
            const downloadLink = paper.download_url || paper.pdf_url || (paper.doi ? `https://doi.org/${paper.doi}` : '#');
            const authors = Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors;
            
            card.innerHTML = `
                <div class="paper-info">
                    <h4 class="paper-title">
                        <a href="${downloadLink}" target="_blank" class="paper-link">
                            ${paper.title || 'Untitled Paper'}
                        </a>
                    </h4>
                    <div class="paper-meta">
                        ${authors ? `<div class="authors">${authors}</div>` : ''}
                        <div class="publisher-year">
                            ${paper.publisher ? `<span class="publisher">${paper.publisher}</span>` : ''}
                            ${paper.year ? `<span class="year">${paper.year}</span>` : ''}
                        </div>
                    </div>
                    ${paper.abstract ? `
                        <div class="paper-abstract">
                            <p>${paper.abstract}</p>
                        </div>
                    ` : ''}
                    <div class="paper-links">
                        ${paper.doi ? `
                            <a href="https://doi.org/${paper.doi}" target="_blank" class="doi-link">
                                <span class="material-icons">link</span>
                                DOI
                            </a>
                        ` : ''}
                        ${paper.download_url ? `
                            <a href="${paper.download_url}" target="_blank" class="download-link">
                                <span class="material-icons">download</span>
                                Download PDF
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
        
        console.log('Papers displayed successfully');
    }

    function displayBooks(container, books) {
        console.log(`Displaying ${books ? books.length : 0} books`);
        console.log('Container element:', container);
        
        if (!books || books.length === 0) {
            console.log('No books to display, showing empty state');
            container.innerHTML = '<div class="empty-state">No books found</div>';
            return;
        }

        console.log('Displaying books:', books);
        container.innerHTML = '';
        
        books.forEach((book, index) => {
            console.log(`Processing book ${index + 1}:`, book);
            
            const card = document.createElement('div');
            card.className = 'book-card';
            
            // Parse authors
            let authors = book.authors;
            if (typeof authors === 'string') {
                authors = authors.split(',').join(', ');
            }
            
            // Format description
            const description = book.description ? book.description.substring(0, 300) + (book.description.length > 300 ? '...' : '') : '';
            
            console.log(`Building HTML for book: ${book.title}`);
            card.innerHTML = `
                <div class="book-cover">
                    ${book.thumbnail ? `<img src="${book.thumbnail}" alt="${book.title}">` : '<div class="no-cover"><span class="material-icons">menu_book</span></div>'}
                </div>
                <div class="book-info">
                    <h4 class="book-title">
                        <a href="${book.info_link}" target="_blank" class="book-link">
                            ${book.title}
                        </a>
                    </h4>
                    ${book.subtitle ? `<div class="book-subtitle">${book.subtitle}</div>` : ''}
                    <div class="book-meta">
                        ${authors ? `<div class="authors">${authors}</div>` : ''}
                        <div class="publisher-year">
                            ${book.publisher ? `<span class="publisher">${book.publisher}</span>` : ''}
                            ${book.published_date ? `<span class="year">${book.published_date.substring(0, 4)}</span>` : ''}
                        </div>
                        ${book.average_rating > 0 ? `
                            <div class="rating">
                                ${formatRating(book.average_rating, book.ratings_count)}
                            </div>
                        ` : ''}
                    </div>
                    ${description ? `
                        <div class="book-description">
                            <p>${description}</p>
                        </div>
                    ` : ''}
                    <div class="book-links">
                        ${book.preview_link ? `
                            <a href="${book.preview_link}" target="_blank" class="preview-link">
                                <span class="material-icons">visibility</span>
                                Preview
                            </a>
                        ` : ''}
                        ${book.buy_link ? `
                            <a href="${book.buy_link}" target="_blank" class="buy-link">
                                <span class="material-icons">shopping_cart</span>
                                Buy
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
            console.log('Appending book card to container');
            container.appendChild(card);
        });
        
        console.log('Books displayed successfully');
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
