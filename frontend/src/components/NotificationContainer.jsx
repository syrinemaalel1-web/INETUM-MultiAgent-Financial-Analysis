import React, { createContext, useContext } from 'react';
import NotificationToast from './NotificationToast';
import { useNotifications } from '../hooks/useNotifications';

// Create notification context
const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
  const notifications = useNotifications();
  
  return (
    <NotificationContext.Provider value={notifications}>
      {children}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.notifications.map((notification) => (
          <NotificationToast
            key={notification.id}
            message={notification.message}
            type={notification.type}
            duration={notification.duration}
            onClose={() => notifications.removeNotification(notification.id)}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export const useNotificationContext = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotificationContext must be used within a NotificationProvider');
  }
  return context;
};

const NotificationContainer = () => {
  const { notifications, removeNotification } = useNotificationContext();

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          message={notification.message}
          type={notification.type}
          duration={notification.duration}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

export default NotificationContainer;