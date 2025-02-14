import React from "react";
import { PhacSignature } from "./PhacSignature.jsx";

const Header = () => {
    return (
        <div className="header-wrapper">
            <header className="App-header">
                <PhacSignature language="en" />
            </header>
        </div>
    );
};

export default Header;
