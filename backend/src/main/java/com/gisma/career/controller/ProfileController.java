package com.gisma.career.controller;

import com.gisma.career.dto.ProfileResponse;
import com.gisma.career.dto.UpdateProfileRequest;
import com.gisma.career.model.Student;
import com.gisma.career.repository.StudentRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/profile")
public class ProfileController {

    private final StudentRepository studentRepository;

    public ProfileController(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    @GetMapping
    public ResponseEntity<ProfileResponse> me(@AuthenticationPrincipal Student student) {
        return ResponseEntity.ok(ProfileResponse.fromEntity(student));
    }

    @PutMapping
    public ResponseEntity<ProfileResponse> update(@AuthenticationPrincipal Student student,
                                                  @RequestBody UpdateProfileRequest req) {
        if (req.getName() != null) student.setName(req.getName());
        if (req.getUniversity() != null) student.setUniversity(req.getUniversity());
        if (req.getCourse() != null) student.setCourse(req.getCourse());
        if (req.getYear() != null) student.setYear(req.getYear());
        Student saved = studentRepository.save(student);
        return ResponseEntity.ok(ProfileResponse.fromEntity(saved));
    }
}
