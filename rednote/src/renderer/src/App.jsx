import React, { useState } from 'react';
import {  DatabaseFilled,  MoonFilled, SunFilled, BookOutlined } from '@ant-design/icons';
import { Tabs, Switch, Space, Divider, Button, Tooltip } from 'antd';

import Home from './pages/Www'


const App = ({ dark, setDark }) => {
  const [xhsUser, setXhsUser] = useState(null);
  // const openXhsBrowser = () => {
  //   window['AppApi'].toggleXhsBrowser();
  // }
  // const [mcpTools, setMcpTools] = useState([]);
  return (
    <Tabs
      defaultActiveKey='about'
      type='card'
      items={[
        {
          key: 'www',
          label: 'MCP Servers',
          icon: <DatabaseFilled />,
          children: <Home xhsUser={xhsUser} setXhsUser={setXhsUser} dark={dark} />
        },
      ]}
      tabBarExtraContent={{
        right: (
          <Space>

           
            <Divider type='vertical' />
            <Tooltip title={`${dark ? 'Light' : 'Dark'}`}>
              <Switch
                checkedChildren={<MoonFilled />}
                unCheckedChildren={<SunFilled />}
                checked={dark}
                onChange={setDark}
              />
            </Tooltip>
          </Space>
        )
      }}
    />
  )
}
export default App;