package com.gisma.career.service;

import com.gisma.career.dto.AuthResponse;
import com.gisma.career.dto.LoginRequest;
import com.gisma.career.dto.SignupRequest;
import com.gisma.career.model.Student;
import com.gisma.career.repository.StudentRepository;
import com.gisma.career.security.JwtUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final StudentRepository studentRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public AuthService(StudentRepository studentRepository,
                       PasswordEncoder passwordEncoder,
                       JwtUtil jwtUtil) {
        this.studentRepository = studentRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil = jwtUtil;
    }

    public AuthResponse signup(SignupRequest req) {
        if (studentRepository.existsByEmail(req.getEmail())) {
            throw new IllegalArgumentException("Email already registered");
        }
        Student s = Student.builder()
                .email(req.getEmail())
                .password(passwordEncoder.encode(req.getPassword()))
                .name(req.getName())
                .university(req.getUniversity())
                .course(req.getCourse())
                .year(req.getYear())
                .build();
        Student saved = studentRepository.save(s);
        String token = jwtUtil.generateToken(saved.getEmail());
        return new AuthResponse(token, saved.getEmail(), saved.getName());
    }

    public AuthResponse login(LoginRequest req) {
        Student s = studentRepository.findByEmail(req.getEmail())
                .orElseThrow(() -> new IllegalArgumentException("Invalid email or password"));
        if (!passwordEncoder.matches(req.getPassword(), s.getPassword())) {
            throw new IllegalArgumentException("Invalid email or password");
        }
        String token = jwtUtil.generateToken(s.getEmail());
        return new AuthResponse(token, s.getEmail(), s.getName());
    }
}
