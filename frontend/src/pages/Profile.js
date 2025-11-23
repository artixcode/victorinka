import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ProfileSidebar from '../components/ProfileSidebar';
import ProfileInfo from '../components/ProfileInfo';
import ProfileHistory from '../components/ProfileHistory';
import ProfileBookmarks from '../components/ProfileBookmarks';
import styles from '../styles/Profile.module.css';

const Profile = () => {
  const [activeSection, setActiveSection] = useState('info');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname;
    if (path.includes('/history')) {
      setActiveSection('history');
    } else if (path.includes('/bookmarks')) {
      setActiveSection('bookmarks');
    } else {
      setActiveSection('info');
    }
  }, [location.pathname]);

  const handleSectionChange = (section) => {
    setActiveSection(section);
    if (section === 'info') {
      navigate('/profile');
    } else {
      navigate(`/profile/${section}`);
    }
  };

  const renderContent = () => {
    switch (activeSection) {
      case 'history':
        return <ProfileHistory />;
      case 'bookmarks':
        return <ProfileBookmarks />;
      default:
        return <ProfileInfo />;
    }
  };

  return (
    <div className={styles.pageContainer}>
      <Header />
      <div className={styles.profilePage}>
        <div className={styles.profileContainer}>
          <div className={styles.profileLayout}>
            <ProfileSidebar
              activeSection={activeSection}
              onSectionChange={handleSectionChange}
            />

            <div className={styles.profileContent}>
              {renderContent()}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Profile;